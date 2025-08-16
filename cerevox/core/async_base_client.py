"""
Async base class for Cerevox SDK clients to reduce code duplication
"""

import asyncio
import base64
import logging
import os
import time
from typing import Any, Dict, Optional

import aiohttp

from .exceptions import (
    LexaError,
    LexaTimeoutError,
    create_error_from_response,
)
from .models import MessageResponse, TokenRefreshRequest, TokenResponse

FAILED_ID = "Failed to get request ID from response"

logger = logging.getLogger(__name__)


class AsyncBaseClient:
    """
    Base class for asynchronous Cerevox API clients

    Provides common functionality including:
    - Async session management
    - HTTP request handling with proper error handling
    - Authentication (_login, _refresh_token, _revoke_token)
    - Async context manager support
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://dev.cerevox.ai/v1",
        max_retries: int = 3,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the async base client

        Args:
            api_key: User Personal Access Token (PAT) for authentication
            base_url: Base URL for the Cerevox API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            **kwargs: Additional aiohttp ClientSession arguments
        """
        self.api_key = api_key or os.getenv("CEREVOX_API_KEY")
        if not self.api_key:
            raise ValueError("api_key is required for authentication")

        # Validate base_url format
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string")

        # Basic URL validation
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")

        # Validate max_retries
        if not isinstance(max_retries, int):
            raise TypeError("max_retries must be an integer")
        if max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")

        self.base_url = base_url.rstrip("/")  # Remove trailing slash
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries

        # Session configuration
        self.session_kwargs = {
            "timeout": self.timeout,
            "headers": {
                "User-Agent": "cerevox-python-async/0.1.6",
                "Content-Type": "application/json",
            },
            **kwargs,
        }

        self.session: Optional[aiohttp.ClientSession] = None

        # Token management attributes
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None

    async def __aenter__(self) -> "AsyncBaseClient":
        """Async context manager entry"""
        await self.start_session()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Async context manager exit"""
        await self.close_session()

    async def start_session(self) -> None:
        """Start the aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(**self.session_kwargs)
            # Automatically authenticate using api_key
            if not self.api_key:
                raise ValueError("API key is required for authentication")
            await self._login(self.api_key)

    async def close_session(self) -> None:
        """Close the aiohttp session"""
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
        skip_auth: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        All requests to API are handled by this method

        Args:
            method: The HTTP method to use
            endpoint: The API endpoint to call
            json_data: JSON data to send in the request body
            params: Query parameters to send in the request
            headers: Additional headers to send with the request
            data: Raw data to send (for file uploads)
            skip_auth: If True, skip token validation (used for auth endpoints)
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the API

        Raises:
            LexaAuthError: If authentication fails
            LexaError: If the request fails for other reasons
            LexaTimeoutError: If the request times out
            Various other LexaError subclasses: Based on response status and content
        """
        if not self.session:
            await self.start_session()

        # Check if token needs refresh before making request (unless this is an auth request)
        if not skip_auth:
            await self._ensure_valid_token()

        url = f"{self.base_url}{endpoint}"

        # Merge additional headers
        request_headers = dict(self.session_kwargs["headers"])
        if headers:
            request_headers.update(headers)

        try:
            async with self.session.request(  # type: ignore
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=request_headers,
                data=data,
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
            logger.error(f"Request timeout for {method} {url}: {e}")
            raise LexaTimeoutError(
                "Request timed out", timeout_duration=self.timeout.total
            ) from e

        except aiohttp.ClientError as e:
            logger.error(f"Request failed for {method} {url}: {e}")
            raise LexaError(f"Request failed: {e}", request_id=FAILED_ID) from e

    # Token Management Methods

    async def _ensure_valid_token(self) -> None:
        """
        Ensure the access token is valid, refreshing if necessary

        Raises:
            LexaError: If token refresh fails
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
        Store token information from authentication response

        Args:
            token_response: Token response containing access token, refresh token, and expiry
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
        Authenticate with api_key to get access tokens

        Args:
            api_key: Personal Access Token scoped to User/Account

        Returns:
            TokenResponse containing access_token, refresh_token, etc.

        Raises:
            LexaAuthError: If authentication fails
        """
        # Use Basic Auth for login
        encoded_credentials = base64.b64encode(api_key.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_credentials}"}

        # Skip token validation for login request
        response_data = await self._request(
            "POST", "/token/login", headers=headers, skip_auth=True
        )

        token_response = TokenResponse(**response_data)

        # Store all token information
        self._store_token_info(token_response)

        return token_response

    async def _refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: The refresh token

        Returns:
            TokenResponse with new tokens
        """
        # Use Basic Auth with API key for refresh (not expired Bearer token)
        if not self.api_key:
            raise LexaError("API key is required for token refresh", request_id=FAILED_ID)
        encoded_credentials = base64.b64encode(self.api_key.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_credentials}"}

        request = TokenRefreshRequest(refresh_token=refresh_token)
        response_data = await self._request(
            "POST",
            "/token/refresh",
            json_data=request.model_dump(),
            headers=headers,
            skip_auth=True,
        )
        token_response = TokenResponse(**response_data)

        # Store all new token information (including new refresh token)
        self._store_token_info(token_response)

        return token_response

    async def _revoke_token(self) -> MessageResponse:
        """
        Revoke the current access token

        Returns:
            MessageResponse with revocation confirmation
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
