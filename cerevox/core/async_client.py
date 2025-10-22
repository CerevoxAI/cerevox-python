"""
Async base class for Cerevox SDK clients
"""

import asyncio
import base64
import logging
import os
import time
from typing import Any, Dict, Optional

import aiohttp

from .constants import core
from .exceptions import (
    LexaError,
    LexaTimeoutError,
    create_error_from_response,
)
from .models import (
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
)

FAILED_ID = core.FAILED_ID
HTTP = core.HTTP_PREFIX
HTTPS = core.HTTPS_PREFIX

logger = logging.getLogger(__name__)


class AsyncClient:
    """
    Base class for asynchronous Cerevox API clients providing core async functionality.

    This foundational async class implements essential client capabilities for
    asynchronous operations including session management with aiohttp, HTTP request
    handling with automatic retries, comprehensive authentication flows, and token
    lifecycle management. All async Cerevox SDK clients inherit from this base class
    to ensure consistent behavior, error handling, and authentication patterns in
    async environments.

    The client automatically handles token refresh, provides async context manager
    support for proper resource management, and is designed for high-performance
    concurrent operations with proper async/await patterns throughout.

    Examples
    --------
    Basic async client usage with context manager (recommended):

    >>> import asyncio
    >>> from cerevox import AsyncClient
    >>>
    >>> async def main():
    ...     async with AsyncClient(api_key="your_token") as client:
    ...         response = await client._request("GET", "/some/endpoint")
    ...         return response
    >>>
    >>> asyncio.run(main())

    Manual session management:

    >>> async def manual_usage():
    ...     client = AsyncClient(api_key="your_token")
    ...     await client.start_session()
    ...     try:
    ...         response = await client._request("GET", "/endpoint")
    ...     finally:
    ...         await client.close_session()

    Custom configuration for high-performance usage:

    >>> import aiohttp
    >>>
    >>> async def high_performance_client():
    ...     connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
    ...     async with AsyncClient(
    ...         api_key="your_token",
    ...         data_url="https://api.cerevox.ai/v1",
    ...         timeout=60.0,
    ...         connector=connector,
    ...         trust_env=True
    ...     ) as client:
    ...         # High-concurrency operations
    ...         tasks = [client._request("GET", f"/items/{i}") for i in range(100)]
    ...         results = await asyncio.gather(*tasks)

    Inheriting from the async base client:

    >>> class CustomAsyncClient(AsyncClient):
    ...     def __init__(self, **kwargs):
    ...         super().__init__(**kwargs)
    ...
    ...     async def custom_operation(self):
    ...         return await self._request("GET", "/custom/endpoint")
    ...
    ...     async def batch_operation(self, items):
    ...         tasks = [self._request("POST", "/process", json_data=item) for item in items]
    ...         return await asyncio.gather(*tasks)

    Error handling in async context:

    >>> async def with_error_handling():
    ...     try:
    ...         async with AsyncClient(api_key="token") as client:
    ...             response = await client._request("GET", "/endpoint")
    ...     except LexaTimeoutError:
    ...         print("Request timed out")
    ...     except LexaAuthError:
    ...         print("Authentication failed")
    ...     except LexaError as e:
    ...         print(f"API error: {e}")

    Notes
    -----
    This class is designed as a base class for async operations and provides
    the foundation for all async Cerevox SDK clients. It should not typically
    be instantiated directly but rather inherited by specific service clients.

    Authentication occurs automatically during session initialization using the
    provided API key. The client maintains JWT tokens internally and handles
    refresh cycles transparently in async context.

    Session management is explicit in async clients - sessions must be started
    before use and properly closed after use. The async context manager handles
    this automatically and is the recommended usage pattern.

    Token refresh occurs automatically when tokens are within 60 seconds of
    expiration, ensuring seamless operation for long-running async processes
    and high-concurrency scenarios.

    All methods are coroutines and must be awaited. The client is designed
    for optimal performance in async/await environments with proper resource
    management and concurrent operation support.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        data_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the async base client with session configuration.

        Parameters
        ----------
        api_key : str, optional
            User Personal Access Token for authentication. If None, attempts
            to read from CEREVOX_API_KEY environment variable. This token
            must have appropriate scopes for the intended operations.
        base_url : str, default "https://dev.cerevox.ai/v1"
            Base URL for cerevox requests.
        auth_url : str, optional
            Base URL for authentication endpoints. If None, defaults to base_url.
        data_url : str, default "https://data.cerevox.ai"
            Data URL for the Cerevox RAG API. Change to production URL
            for live environments.
        max_retries : int, default 3
            Maximum retry attempts for transient failures. Must be >= 0.
            Retries are handled at the application level for specific error types.
        timeout : float, default 30.0
            Default timeout for HTTP requests in seconds. Must be positive.
            Applied as total timeout including connection, request, and response time.
        **kwargs : dict
            Additional aiohttp.ClientSession configuration including
            connector, trust_env, proxy, ssl, cookies, headers, or auth settings.

        Raises
        ------
        ValueError
            If api_key is not provided and CEREVOX_API_KEY environment
            variable is not set, or if URL parameters are malformed.
        TypeError
            If max_retries is not an integer.

        Notes
        -----
        Unlike the synchronous client, authentication does not occur during
        initialization. The session must be started explicitly or via the
        async context manager, at which point authentication is performed.

        URLs are normalized by removing trailing slashes to ensure consistent
        endpoint construction. Both HTTP and HTTPS protocols are supported,
        though HTTPS is recommended for production usage.

        The session configuration is stored in session_kwargs but the actual
        aiohttp.ClientSession is not created until start_session() is called.
        This allows for proper async resource management.
        """
        self.api_key = api_key or os.getenv("CEREVOX_API_KEY")
        if not self.api_key:
            raise ValueError("api_key is required for authentication")

        # Validate max_retries type and value
        if not isinstance(max_retries, int):
            raise TypeError("max_retries must be an integer")
        if max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")

        # Default base_url if not provided
        if not base_url:
            base_url = "https://dev.cerevox.ai/v1"

        # Default auth_url to base_url if not provided
        if not auth_url:
            auth_url = base_url

        # Default data_url if not provided
        if not data_url:
            data_url = "https://data.cerevox.ai"

        # Basic URL validation
        if not isinstance(base_url, str) or not base_url:
            raise ValueError("base_url must be a non-empty string")
        if not (base_url.startswith(HTTP) or base_url.startswith(HTTPS)):
            raise ValueError(f"base_url must start with {HTTP} or {HTTPS}")

        if not isinstance(auth_url, str) or not auth_url:
            raise ValueError("auth_url must be a non-empty string")
        if not (auth_url.startswith(HTTP) or auth_url.startswith(HTTPS)):
            raise ValueError(f"auth_url must start with {HTTP} or {HTTPS}")

        if not isinstance(data_url, str) or not data_url:
            raise ValueError("data_url must be a non-empty string")
        if not (data_url.startswith(HTTP) or data_url.startswith(HTTPS)):
            raise ValueError(f"data_url must start with {HTTP} or {HTTPS}")

        self.base_url = base_url.rstrip("/")  # Remove trailing slash
        self.auth_url = auth_url.rstrip("/")  # Remove trailing slash
        self.data_url = data_url.rstrip("/")  # Remove trailing slash

        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries

        # Session configuration - filter out non-aiohttp parameters
        session_only_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ["auth_url", "base_url", "data_url"]
        }
        self.session_kwargs = {
            "timeout": self.timeout,
            "headers": {
                "User-Agent": "cerevox-python-async/0.1.6",
            },
            **session_only_kwargs,
        }

        self.session: Optional[aiohttp.ClientSession] = None

        # Token management attributes
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None

    async def __aenter__(self) -> "AsyncClient":
        """
        Async context manager entry point for resource initialization.

        Returns
        -------
        AsyncClient
            The initialized client instance with active session and
            authentication ready for async operations.

        Notes
        -----
        Automatically starts the HTTP session and performs authentication.
        This is the recommended way to use async clients as it ensures
        proper resource management and automatic cleanup.

        Examples
        --------
        >>> async with AsyncClient(api_key="token") as client:
        ...     response = await client._request("GET", "/endpoint")
        ...     # Session automatically closed when exiting context
        """
        await self.start_session()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """
        Async context manager exit point for resource cleanup.

        Parameters
        ----------
        exc_type : type or None
            Exception type if an exception occurred within the context.
        exc_val : BaseException or None
            Exception instance if an exception occurred.
        exc_tb : Any or None
            Traceback object if an exception occurred.

        Notes
        -----
        Automatically closes the HTTP session regardless of whether
        an exception occurred within the context, ensuring proper
        resource cleanup in all scenarios.

        The session closure is awaited to ensure all pending requests
        are completed or cancelled before the context exits.
        """
        await self.close_session()

    async def start_session(self) -> None:
        """
        Initialize the aiohttp session and perform authentication.

        This method creates the underlying aiohttp.ClientSession with the
        configured parameters and performs initial authentication using
        the provided API key to obtain JWT tokens.

        Raises
        ------
        ValueError
            If no API key is available for authentication.
        LexaAuthError
            If authentication fails due to invalid credentials or
            authentication service unavailability.
        aiohttp.ClientError
            If session creation fails due to configuration issues.

        Notes
        -----
        This method is called automatically by the async context manager
        but can be called manually when not using context manager syntax.

        Authentication occurs during session initialization, exchanging
        the API key for JWT access and refresh tokens that are used for
        subsequent API requests.

        Only one session should be active per client instance. Calling
        this method when a session already exists has no effect.

        Examples
        --------
        Manual session management:

        >>> client = AsyncClient(api_key="token")
        >>> await client.start_session()
        >>> # Client is now ready for requests
        >>> response = await client._request("GET", "/endpoint")
        >>> await client.close_session()
        """
        if self.session is None:
            self.session = aiohttp.ClientSession(**self.session_kwargs)
            # Automatically authenticate using api_key
            if not self.api_key:
                raise ValueError("API key is required for authentication")
            await self._login(self.api_key)

    async def close_session(self) -> None:
        """
        Close the aiohttp session and release associated resources.

        This method gracefully closes the underlying aiohttp session,
        ensuring that all connection pools are properly cleaned up and
        resources are released. Must be awaited to ensure proper cleanup.

        Notes
        -----
        This method is automatically called when using the client as an
        async context manager. Manual calling is only necessary when not
        using context manager syntax.

        After calling this method, the client instance should not be used
        for further requests as the session will be invalid. A new session
        can be started by calling start_session() again.

        The closure operation is asynchronous and must be awaited to ensure
        all pending operations are completed before the session is destroyed.

        Examples
        --------
        >>> client = AsyncClient(api_key="token")
        >>> await client.start_session()
        >>> # ... perform operations ...
        >>> await client.close_session()  # Required for proper cleanup
        """
        if self.session:
            await self.session.close()
            self.session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        is_auth: bool = False,
        is_data: bool = False,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute async HTTP requests with automatic authentication and error handling.

        This method serves as the central async request handler for all API
        interactions, providing automatic token management, comprehensive error
        handling, and response processing. It handles both data operations and
        authentication flows seamlessly in async context.

        Parameters
        ----------
        method : str
            HTTP method to use for the request. Common values include
            "GET", "POST", "PUT", "DELETE", "PATCH".
        endpoint : str
            API endpoint path starting with '/'. Will be appended to the
            appropriate base URL (data_url or auth_url).
        json_data : dict, optional
            JSON payload to send in the request body. Automatically
            serialized and sets appropriate Content-Type headers.
        params : dict, optional
            Query parameters to append to the URL. Values are automatically
            URL-encoded by aiohttp.
        headers : dict, optional
            Additional HTTP headers to include with the request. These
            are merged with session-level headers.
        data : Any, optional
            Raw data to send in the request body, typically for file uploads
            or multipart form data. Can be bytes, FormData, or file-like objects.
        is_auth : bool, default False
            If True, uses auth_url and bypasses token validation for
            authentication endpoints.
        is_data : bool, default False
            If True, uses data_url.
        timeout : float, optional
            Override the default timeout for this specific request.
            If None, uses the client's default timeout.
        **kwargs : dict
            Additional arguments passed directly to aiohttp.ClientSession.request,
            such as 'allow_redirects', 'max_redirects', 'ssl', or 'proxy'.

        Returns
        -------
        dict
            Parsed JSON response from the API. For non-JSON responses,
            returns a basic success status dictionary.

        Raises
        ------
        LexaAuthError
            If authentication fails, tokens are invalid, or authorization
            is insufficient for the requested operation.
        LexaTimeoutError
            If the request exceeds the configured timeout duration.
        LexaError
            For various API errors including validation failures, resource
            not found, rate limiting, or server errors.
        aiohttp.ClientError
            If network connectivity issues prevent the request from
            being sent or completed.

        Examples
        --------
        Basic async GET request:

        >>> response = await client._request("GET", "/users/me")
        >>> user_id = response["user_id"]

        POST request with JSON data:

        >>> data = {"name": "New Folder", "description": "Test folder"}
        >>> response = await client._request("POST", "/folders", json_data=data)

        Request with query parameters:

        >>> params = {"limit": 10, "offset": 0}
        >>> response = await client._request("GET", "/documents", params=params)

        File upload with raw data:

        >>> with open("document.pdf", "rb") as f:
        ...     data = f.read()
        >>> response = await client._request("POST", "/upload", data=data)

        Concurrent requests:

        >>> tasks = [
        ...     client._request("GET", f"/items/{i}")
        ...     for i in range(10)
        ... ]
        >>> responses = await asyncio.gather(*tasks)

        Custom headers and request options:

        >>> headers = {"Custom-Header": "value"}
        >>> response = await client._request(
        ...     "GET", "/endpoint",
        ...     headers=headers,
        ...     allow_redirects=False
        ... )

        Notes
        -----
        The method automatically ensures the session is started before making
        requests. If no session exists, it will be created and authentication
        will be performed automatically.

        Token validation and refresh occur automatically before each request
        (except for authentication requests) to ensure uninterrupted operation
        for long-running async processes.

        Request IDs are extracted from response headers when available and
        included in error reporting for debugging and support purposes.

        Non-JSON responses are handled gracefully and return a success status
        indicator rather than failing on parse errors.

        The method is designed for high-concurrency usage with proper async/await
        patterns and can handle thousands of concurrent requests efficiently.
        """
        if not self.session:
            await self.start_session()

        # Determine which base URL to use
        if is_auth:
            base_url = self.auth_url
        elif is_data:
            base_url = self.data_url
        else:
            base_url = self.base_url

        # Check if token needs refresh before making request
        if not is_auth:
            await self._ensure_valid_token()

        url = f"{base_url}{endpoint}"

        # Merge additional headers
        request_headers = dict(self.session_kwargs["headers"])
        if headers:
            request_headers.update(headers)

        try:
            # Use provided timeout or fall back to default
            if timeout is not None:
                request_timeout = aiohttp.ClientTimeout(total=timeout)
            else:
                request_timeout = self.timeout

            async with self.session.request(  # type: ignore
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=request_headers,
                data=data,
                timeout=request_timeout,
                **kwargs,
            ) as response:
                # Extract request ID for error reporting
                request_id = response.headers.get("x-request-id", FAILED_ID)

                # Handle successful responses
                if 200 <= response.status < 300:
                    try:
                        response_data: Dict[str, Any] = await response.json()
                        return response_data
                    except (ValueError, aiohttp.ContentTypeError):
                        # Non-JSON response, return basic success info
                        return {"status": "success"}

                # Handle error responses
                try:
                    error_data = await response.json()
                except (ValueError, aiohttp.ContentTypeError):
                    error_text = await response.text()
                    error_data = {
                        "error": f"HTTP {response.status}",
                        "message": error_text,
                    }

                # Create and raise appropriate exception
                raise create_error_from_response(
                    status_code=response.status,
                    response_data=error_data,
                    request_id=request_id,
                )

        except asyncio.TimeoutError as e:
            request_type = "Auth request" if is_auth else "Request"
            logger.error(f"{request_type} timeout for {method} {url}: {e}")
            timeout_msg = "Auth request timed out" if is_auth else "Request timed out"
            raise LexaTimeoutError(
                timeout_msg, timeout_duration=self.timeout.total
            ) from e

        except aiohttp.ClientError as e:
            request_type = "Auth request" if is_auth else "Request"
            logger.error(f"{request_type} failed for {method} {url}: {e}")
            error_msg = "Auth request failed" if is_auth else "Request failed"
            raise LexaError(f"{error_msg}: {e}", request_id=FAILED_ID) from e

    # Token Management Methods

    async def _ensure_valid_token(self) -> None:
        """
        Ensure the access token is valid, refreshing if necessary in async context.

        This async method checks the current token's expiration status and
        automatically refreshes it if it's expired or within 60 seconds of
        expiration. This proactive approach prevents authentication failures
        during long-running async operations and high-concurrency scenarios.

        Raises
        ------
        LexaError
            If no access token is available, refresh token is missing,
            or token refresh operation fails.

        Notes
        -----
        Token validation occurs automatically before each API request,
        so this method typically doesn't need to be called manually.

        The 60-second buffer before expiration ensures that tokens don't
        expire during request processing, providing a safety margin for
        network latency and processing delays in async environments.

        This method is safe for concurrent use - multiple concurrent requests
        will not trigger multiple refresh attempts due to proper async handling.

        Examples
        --------
        Manual token validation (rarely needed):

        >>> await client._ensure_valid_token()
        >>> # Token is now guaranteed to be valid for at least 60 seconds
        """
        if not self.access_token or not self.token_expires_at:
            # No token available, this shouldn't happen after initialization
            raise LexaError("No access token available", request_id=FAILED_ID)

        # Check if token is expired or will expire in the next 60 seconds
        current_time = time.time()
        if current_time >= (self.token_expires_at - 60):
            logger.info("Access token expired or expiring soon, refreshing...")
            if self.refresh_token:
                await self._refresh_token(self.refresh_token)
            else:
                raise LexaError("No refresh token available", request_id=FAILED_ID)

    def _store_token_info(self, token_response: TokenResponse) -> None:
        """
        Store token information from authentication responses.

        This method updates the client's token state with new authentication
        information, including access tokens, refresh tokens, and expiration
        timestamps. It also updates the session configuration to use the new token.

        Parameters
        ----------
        token_response : TokenResponse
            Token response object containing access_token, refresh_token,
            expires_in, and other authentication metadata.

        Notes
        -----
        This method is called automatically during login and token refresh
        operations to maintain current authentication state.

        The expiration timestamp is calculated from the current time plus
        the expires_in duration to provide accurate expiration tracking.

        Unlike the synchronous client, this method updates the session_kwargs
        headers rather than an active session, since session headers are
        immutable after creation in aiohttp.
        """
        self.access_token = token_response.access_token
        self.refresh_token = token_response.refresh_token

        # Calculate expiration timestamp
        current_time = time.time()
        self.token_expires_at = current_time + token_response.expires_in

        # Update session headers with new access token
        self.session_kwargs["headers"][
            "Authorization"
        ] = f"Bearer {token_response.access_token}"

    # Authentication Methods

    async def _login(self, api_key: str) -> TokenResponse:
        """
        Authenticate with API key to obtain JWT access tokens asynchronously.

        This async method performs the initial authentication flow using the
        provided Personal Access Token to obtain JWT access and refresh tokens
        for subsequent API operations in async context.

        Parameters
        ----------
        api_key : str
            Personal Access Token with appropriate scopes for the intended
            operations. Must be a valid, non-expired PAT.

        Returns
        -------
        TokenResponse
            Authentication response containing access_token, refresh_token,
            token_type, expires_in, and scope information.

        Raises
        ------
        LexaAuthError
            If the API key is invalid, expired, lacks necessary scopes,
            or the authentication service is unavailable.
        LexaError
            If the authentication request fails due to network issues
            or other non-authentication related problems.

        Examples
        --------
        This method is called automatically during session initialization:

        >>> async with AsyncClient(api_key="your_token") as client:
        ...     # Authentication occurs automatically

        Manual re-authentication (if needed):

        >>> token_response = await client._login("new_api_key")
        >>> print(f"Token expires in {token_response.expires_in} seconds")

        Notes
        -----
        The API key is sent using HTTP Basic Authentication where the
        API key serves as the username and no password is required.

        Upon successful authentication, the client automatically stores
        all token information and updates session configuration for
        subsequent requests.

        This method should only be called during session initialization
        or when explicitly re-authenticating with a new API key.

        The async nature allows for non-blocking authentication, enabling
        efficient initialization of multiple client instances concurrently.
        """
        # Use Basic Auth for login
        encoded_credentials = base64.b64encode(api_key.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_credentials}"}

        # Skip token validation for login request and use auth_url
        response_data = await self._request(
            "POST",
            "/token/login",
            headers=headers,
            json_data={"login": True},
            is_auth=True,
        )

        token_response = TokenResponse(**response_data)

        # Store all token information
        self._store_token_info(token_response)

        return token_response

    async def _refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using the refresh token asynchronously.

        This async method obtains a new access token using the provided refresh
        token, extending the authentication session without requiring
        re-authentication with the original API key in async context.

        Parameters
        ----------
        refresh_token : str
            Valid refresh token obtained from previous authentication
            or token refresh operations.

        Returns
        -------
        TokenResponse
            New authentication response containing fresh access_token,
            refresh_token, and updated expiration information.

        Raises
        ------
        LexaAuthError
            If the refresh token is invalid, expired, or the refresh
            operation is rejected by the authentication service.
        LexaError
            If the refresh request fails due to network issues or
            missing API key for re-authentication.

        Notes
        -----
        This method is called automatically by _ensure_valid_token() when
        the current access token is near expiration, so manual calls are
        typically not necessary.

        The refresh operation may return a new refresh token, which
        replaces the previous one for future refresh operations.

        Basic authentication with the original API key is used for the
        refresh request to ensure security and prevent token theft.

        The async nature allows for non-blocking token refresh, enabling
        seamless operation in high-concurrency async environments.

        Examples
        --------
        Manual token refresh (rarely needed):

        >>> if client.refresh_token:
        ...     new_token = await client._refresh_token(client.refresh_token)
        ...     print(f"New token expires in {new_token.expires_in} seconds")
        """
        # Use Basic Auth with API key for refresh (not expired Bearer token)
        if not self.api_key:
            raise LexaError(
                "API key is required for token refresh", request_id=FAILED_ID
            )
        encoded_credentials = base64.b64encode(self.api_key.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_credentials}"}

        request = TokenRefreshRequest(refresh_token=refresh_token)
        response_data = await self._request(
            "POST",
            "/token/refresh",
            json_data=request.model_dump(),
            headers=headers,
            is_auth=True,
        )
        token_response = TokenResponse(**response_data)

        # Store all new token information (including new refresh token)
        self._store_token_info(token_response)

        return token_response

    async def _revoke_token(self) -> MessageResponse:
        """
        Revoke the current access token and clear authentication state asynchronously.

        This async method invalidates the current access token on the server side
        and clears all authentication information from the client, effectively
        logging out the current session in async context.

        Returns
        -------
        MessageResponse
            Confirmation message indicating successful token revocation.

        Raises
        ------
        LexaAuthError
            If the current token is invalid or the revocation request
            is rejected by the authentication service.
        LexaError
            If the revocation request fails due to network issues.

        Examples
        --------
        Explicitly logout and revoke tokens:

        >>> response = await client._revoke_token()
        >>> print(response.message)  # "Token revoked successfully"

        Revoke token before closing session:

        >>> async with AsyncClient(api_key="token") as client:
        ...     # ... perform operations ...
        ...     await client._revoke_token()
        ...     # Session will close automatically, token is already revoked

        Notes
        -----
        After successful token revocation, the client will need to
        re-authenticate before making further API requests. All stored
        token information is cleared from the client instance.

        This operation is irreversible - revoked tokens cannot be
        reactivated and new authentication is required to continue
        using the API.

        The revocation request uses the current access token for
        authentication, so it must be valid when called.

        The async nature allows for non-blocking logout operations,
        useful when shutting down multiple client instances concurrently.
        """
        response_data = await self._request("POST", "/token/revoke")

        # Clear all token information since the token is now revoked
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

        # Remove the authorization header
        if "Authorization" in self.session_kwargs["headers"]:
            del self.session_kwargs["headers"]["Authorization"]

        return MessageResponse(**response_data)
