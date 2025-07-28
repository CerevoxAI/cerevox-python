"""
Async base class for Cerevox SDK clients to reduce code duplication
"""

import asyncio
import base64
import logging
import os
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
    - Authentication (login, refresh_token, revoke_token)
    - Async context manager support
    """

    def __init__(
        self,
        *,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://dev.cerevox.ai/v1",
        max_retries: int = 3,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the async base client

        Args:
            email: User email address for authentication
            api_key: User password for authentication
            base_url: Base URL for the Cerevox API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            **kwargs: Additional aiohttp ClientSession arguments
        """
        self.email = email
        self.api_key = api_key or os.getenv("CEREVOX_API_KEY")
        if not self.email or not self.api_key:
            raise ValueError("Both email and api_key are required for authentication")

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
            # Automatically authenticate using email and password
            await self.login(self.email, self.api_key)

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

    # Authentication Methods

    async def login(
        self, email: Optional[str] = None, password: Optional[str] = None
    ) -> TokenResponse:
        """
        Authenticate with email and password to get access tokens

        Args:
            email: User email address
            password: User password

        Returns:
            TokenResponse containing access_token, refresh_token, etc.

        Raises:
            LexaAuthError: If authentication fails
        """
        # Use Basic Auth for login
        credentials = f"{email}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_credentials}"}

        response_data = await self._request(
            "POST", "/token/login", json_data={}, headers=headers
        )

        token_response = TokenResponse(**response_data)

        self.session_kwargs["headers"][
            "Authorization"
        ] = f"Bearer {token_response.access_token}"

        return token_response

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: The refresh token

        Returns:
            TokenResponse with new tokens
        """
        request = TokenRefreshRequest(refresh_token=refresh_token)
        response_data = await self._request(
            "POST", "/token/refresh", json_data=request.model_dump()
        )
        token_response = TokenResponse(**response_data)

        self.session_kwargs["headers"][
            "Authorization"
        ] = f"Bearer {token_response.access_token}"

        return token_response

    async def revoke_token(self) -> MessageResponse:
        """
        Revoke the current access token

        Returns:
            MessageResponse with revocation confirmation
        """
        response_data = await self._request("POST", "/token/revoke")

        # Remove the authorization header since the token is now revoked
        if "Authorization" in self.session_kwargs["headers"]:
            del self.session_kwargs["headers"]["Authorization"]

        return MessageResponse(**response_data)
