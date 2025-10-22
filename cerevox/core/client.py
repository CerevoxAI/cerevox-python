"""
Base class for Cerevox SDK clients
"""

import base64
import logging
import os
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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


class Client:
    """
    Base class for synchronous Cerevox API clients providing core functionality.

    This foundational class implements essential client capabilities including
    session management with connection pooling, HTTP request handling with
    automatic retries, comprehensive authentication flows, and token lifecycle
    management. All Cerevox SDK clients inherit from this base class to ensure
    consistent behavior, error handling, and authentication patterns.

    The client automatically handles token refresh, request retries for transient
    failures, and provides both standalone usage and context manager support
    for proper resource management.

    Examples
    --------
    Basic client initialization and usage:

    >>> from cerevox import Client
    >>> client = Client(api_key="your_pat_token")
    >>> # Client automatically authenticates during initialization
    >>> response = client._request("GET", "/some/endpoint")

    Using context manager for automatic cleanup:

    >>> with Client(api_key="your_token") as client:
    ...     response = client._request("GET", "/endpoint")
    ...     # Session automatically closed when exiting context

    Custom configuration with retries and timeouts:

    >>> client = Client(
    ...     api_key="your_token",
    ...     data_url="https://api.cerevox.ai/v1",
    ...     max_retries=5,
    ...     timeout=60.0,
    ...     session_kwargs={"verify": True, "proxies": {"https": "proxy:8080"}}
    ... )

    Inheriting from the base client:

    >>> class CustomClient(Client):
    ...     def __init__(self, **kwargs):
    ...         super().__init__(**kwargs)
    ...
    ...     def custom_operation(self):
    ...         return self._request("GET", "/custom/endpoint")

    Notes
    -----
    This class is designed as a base class and provides the foundation for
    all Cerevox SDK clients. It should not typically be instantiated directly
    but rather inherited by specific service clients.

    Authentication occurs automatically during initialization using the provided
    API key. The client maintains JWT tokens internally and handles refresh
    cycles transparently.

    The retry strategy targets transient failures (5xx errors) and uses
    exponential backoff. Client errors (4xx) are not retried as they
    typically indicate permanent issues requiring user intervention.

    Token refresh occurs automatically when tokens are within 60 seconds
    of expiration, ensuring seamless operation for long-running processes.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        data_url: Optional[str] = None,
        max_retries: int = 3,
        session_kwargs: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the base client with authentication and session configuration.

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
            Applies to 5xx server errors with exponential backoff strategy.
        session_kwargs : dict, optional
            Additional configuration for the requests.Session instance.
            Common options include 'verify', 'proxies', 'cert', 'stream'.
        timeout : float, default 30.0
            Default timeout for HTTP requests in seconds. Must be positive.
            Individual requests may override this value.
        **kwargs : dict
            Additional session configuration parameters applied directly
            to the session instance for backward compatibility.

        Raises
        ------
        ValueError
            If api_key is not provided and CEREVOX_API_KEY environment
            variable is not set, or if URL parameters are malformed.
        LexaAuthError
            If initial authentication fails due to invalid credentials
            or authentication service unavailability.
        LexaError
            If session initialization fails due to network or configuration issues.

        Notes
        -----
        Authentication occurs automatically during initialization. The client
        exchanges the API key for JWT access and refresh tokens, which are
        managed transparently throughout the session lifecycle.

        URLs are normalized by removing trailing slashes to ensure consistent
        endpoint construction. Both HTTP and HTTPS protocols are supported,
        though HTTPS is recommended for production usage.

        The session is configured with a retry strategy that handles transient
        server errors (5xx status codes) but not client errors (4xx), which
        typically require user intervention to resolve.
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

        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize session
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[500, 501, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=0.1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount(HTTP, adapter)
        self.session.mount(HTTPS, adapter)

        # Set default headers
        self.session.headers.update(
            {
                "User-Agent": "cerevox-python/0.1.6",
            }
        )

        # Apply session configuration
        if session_kwargs:
            for key, value in session_kwargs.items():
                setattr(self.session, key, value)

        # Apply any additional session configuration for backward compatibility
        for key, value in kwargs.items():
            setattr(self.session, key, value)

        # Token management attributes
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None

        # Automatically authenticate using api_key
        self._login(self.api_key)

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        is_auth: bool = False,
        is_data: bool = False,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute HTTP requests with automatic authentication and error handling.

        This method serves as the central request handler for all API interactions,
        providing automatic token management, request retry logic, comprehensive
        error handling, and response processing. It handles both data operations
        and authentication flows seamlessly.

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
            URL-encoded.
        headers : dict, optional
            Additional HTTP headers to include with the request. These
            are merged with session-level headers.
        files : dict, optional
            Files to upload in multipart/form-data format. Keys are field
            names, values are file-like objects or tuples.
        is_auth : bool, default False
            If True, uses base_url and bypasses token validation for
            authentication endpoints.
        is_data : bool, default False
            If True, uses data_url.
        timeout : float, optional
            Override the default timeout for this specific request.
            If None, uses the client's default timeout.
        **kwargs : dict
            Additional arguments passed directly to the requests library,
            such as 'stream', 'allow_redirects', or 'verify'.

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
        ConnectionError
            If network connectivity issues prevent the request from
            being sent or completed.

        Examples
        --------
        Basic GET request:

        >>> response = client._request("GET", "/users/me")
        >>> user_id = response["user_id"]

        POST request with JSON data:

        >>> data = {"name": "New Folder", "description": "Test folder"}
        >>> response = client._request("POST", "/folders", json_data=data)

        Request with query parameters:

        >>> params = {"limit": 10, "offset": 0}
        >>> response = client._request("GET", "/documents", params=params)

        File upload request:

        >>> with open("document.pdf", "rb") as f:
        ...     files = {"file": f}
        ...     response = client._request("POST", "/upload", files=files)

        Custom headers and timeout:

        >>> headers = {"Custom-Header": "value"}
        >>> response = client._request(
        ...     "GET", "/endpoint",
        ...     headers=headers,
        ...     timeout=60.0
        ... )

        Notes
        -----
        The method automatically handles token refresh if the current token
        is expired or within 60 seconds of expiration. This ensures
        uninterrupted operation for long-running processes.

        Request IDs are extracted from response headers when available and
        included in error reporting for debugging and support purposes.

        Non-JSON responses are handled gracefully and return a success
        status indicator rather than failing on parse errors.

        The retry strategy applies only to server errors (5xx) and does
        not retry client errors (4xx) which typically require user
        intervention to resolve.
        """
        # Determine which base URL to use
        if is_auth:
            base_url = self.auth_url if hasattr(self, "auth_url") else self.data_url
        elif is_data:
            base_url = self.data_url
        else:
            # Fallback to data_url if base_url is not set (for backward compatibility with tests)
            base_url = self.base_url if hasattr(self, "base_url") else self.data_url

        # Check if token needs refresh before making request
        if not is_auth:
            self._ensure_valid_token()

        url = f"{base_url}{endpoint}"

        # Merge additional headers
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)

        try:
            # Use provided timeout or fall back to default
            request_timeout = timeout if timeout is not None else self.timeout

            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=request_headers,
                files=files,
                timeout=request_timeout,
                **kwargs,
            )

            # Extract request ID for error reporting
            request_id = response.headers.get("x-request-id", FAILED_ID)

            # Handle successful responses
            if 200 <= response.status_code < 300:
                try:
                    response_data: Dict[str, Any] = response.json()
                    return response_data
                except ValueError:
                    # Non-JSON response, return basic success info
                    return {"status": "success"}

            # Handle error responses
            try:
                error_data = response.json()
            except ValueError:
                error_data = {
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                }

            # Create and raise appropriate exception
            raise create_error_from_response(
                status_code=response.status_code,
                response_data=error_data,
                request_id=request_id,
            )

        except requests.exceptions.Timeout as e:
            request_type = "Auth request" if is_auth else "Request"
            logger.error(f"{request_type} timeout for {method} {url}: {e}")
            timeout_msg = "Auth request timed out" if is_auth else "Request timed out"
            raise LexaTimeoutError(timeout_msg, timeout_duration=self.timeout) from e

        except requests.exceptions.RequestException as e:
            request_type = "Auth request" if is_auth else "Request"
            logger.error(f"{request_type} failed for {method} {url}: {e}")
            error_msg = "Auth request failed" if is_auth else "Request failed"
            raise LexaError(f"{error_msg}: {e}", request_id=FAILED_ID) from e

    def close(self) -> None:
        """
        Close the HTTP session and release associated resources.

        This method gracefully closes the underlying requests session,
        ensuring that connection pools are properly cleaned up and
        resources are released. Should be called when the client is
        no longer needed.

        Notes
        -----
        This method is automatically called when using the client as
        a context manager. Manual calling is only necessary when not
        using context manager syntax.

        After calling this method, the client instance should not be
        used for further requests as the session will be invalid.
        """
        if hasattr(self, "session"):
            self.session.close()

    def __enter__(self) -> "Client":
        """
        Context manager entry point for resource management.

        Returns
        -------
        Client
            The client instance ready for use within the context.

        Examples
        --------
        >>> with Client(api_key="token") as client:
        ...     response = client._request("GET", "/endpoint")
        ...     # Session automatically closed when exiting
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Context manager exit point for automatic resource cleanup.

        Parameters
        ----------
        exc_type : type or None
            Exception type if an exception occurred within the context.
        exc_val : Exception or None
            Exception instance if an exception occurred.
        exc_tb : traceback or None
            Traceback object if an exception occurred.

        Notes
        -----
        Automatically closes the HTTP session regardless of whether
        an exception occurred within the context, ensuring proper
        resource cleanup in all scenarios.
        """
        self.close()

    # Token Management Methods

    def _ensure_valid_token(self) -> None:
        """
        Ensure the access token is valid, refreshing if necessary.

        This method checks the current token's expiration status and
        automatically refreshes it if it's expired or within 60 seconds
        of expiration. This proactive approach prevents authentication
        failures during long-running operations.

        Raises
        ------
        LexaError
            If no access token is available, refresh token is missing,
            or token refresh operation fails.

        Notes
        -----
        Token validation occurs automatically before each API request,
        so this method typically doesn't need to be called manually.

        The 60-second buffer before expiration ensures that tokens
        don't expire during request processing, providing a safety
        margin for network latency and processing delays.
        """
        if not self.access_token or not self.token_expires_at:
            # No token available, this shouldn't happen after initialization
            raise LexaError("No access token available", request_id=FAILED_ID)

        # Check if token is expired or will expire in the next 60 seconds
        current_time = time.time()
        if current_time >= (self.token_expires_at - 60):
            logger.info("Access token expired or expiring soon, refreshing...")
            if self.refresh_token:
                self._refresh_token(self.refresh_token)
            else:
                raise LexaError("No refresh token available", request_id=FAILED_ID)

    def _store_token_info(self, token_response: TokenResponse) -> None:
        """
        Store token information from authentication responses.

        This method updates the client's token state with new authentication
        information, including access tokens, refresh tokens, and expiration
        timestamps. It also updates the session headers to use the new token.

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
        """
        self.access_token = token_response.access_token
        self.refresh_token = token_response.refresh_token

        # Calculate expiration timestamp
        current_time = time.time()
        self.token_expires_at = current_time + token_response.expires_in

        # Update session headers with new access token
        self.session.headers.update(
            {"Authorization": f"Bearer {token_response.access_token}"}
        )

    # Authentication Methods

    def _login(self, api_key: str) -> TokenResponse:
        """
        Authenticate with API key to obtain JWT access tokens.

        This method performs the initial authentication flow using the
        provided Personal Access Token to obtain JWT access and refresh
        tokens for subsequent API operations.

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
        This method is called automatically during client initialization:

        >>> client = Client(api_key="your_pat_token")
        >>> # Authentication occurs automatically

        Manual re-authentication (if needed):

        >>> token_response = client._login("new_api_key")
        >>> print(f"Token expires in {token_response.expires_in} seconds")

        Notes
        -----
        The API key is sent using HTTP Basic Authentication where the
        API key serves as the username and no password is required.

        Upon successful authentication, the client automatically stores
        all token information and updates session headers for subsequent
        requests.

        This method should only be called during initialization or when
        explicitly re-authenticating with a new API key.
        """
        # Use Basic Auth for login
        encoded_credentials = base64.b64encode(api_key.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_credentials}"}

        # Skip token validation for login request and use auth_url
        response_data = self._request(
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

    def _refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using the refresh token.

        This method obtains a new access token using the provided refresh
        token, extending the authentication session without requiring
        re-authentication with the original API key.

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
        """
        # Use Basic Auth with API key for refresh (not expired Bearer token)
        if not self.api_key:
            raise LexaError(
                "API key is required for token refresh", request_id=FAILED_ID
            )
        encoded_credentials = base64.b64encode(self.api_key.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_credentials}"}

        request = TokenRefreshRequest(refresh_token=refresh_token)
        response_data = self._request(
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

    def _revoke_token(self) -> MessageResponse:
        """
        Revoke the current access token and clear authentication state.

        This method invalidates the current access token on the server side
        and clears all authentication information from the client, effectively
        logging out the current session.

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

        >>> response = client._revoke_token()
        >>> print(response.message)  # "Token revoked successfully"

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
        """
        response_data = self._request("POST", "/token/revoke")

        # Clear all token information since the token is now revoked
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

        # Remove the authorization header
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]

        return MessageResponse(**response_data)
