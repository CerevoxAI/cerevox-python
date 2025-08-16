"""
Base classes for Cerevox SDK clients to reduce code duplication
"""

import base64
import logging
import os
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    LexaError,
    LexaTimeoutError,
    create_error_from_response,
)
from .models import MessageResponse, TokenRefreshRequest, TokenResponse

HTTP = "http://"
HTTPS = "https://"
FAILED_ID = "Failed to get request ID from response"

logger = logging.getLogger(__name__)


class BaseClient:
    """
    Base class for synchronous Cerevox API clients

    Provides common functionality including:
    - Session management with connection pooling
    - HTTP request handling with retries
    - Authentication (_login, _refresh_token, _revoke_token)
    - Context manager support
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://dev.cerevox.ai/v1",
        auth_url: Optional[str] = None,
        max_retries: int = 3,
        session_kwargs: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the base client

        Args:
            api_key: User Personal Access Token (PAT) for authentication
            base_url: Base URL for the Cerevox API (used for data requests)
            auth_url: Base URL for authentication (defaults to base_url if not provided)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            session_kwargs: Additional arguments to pass to requests.Session
        """
        self.api_key = api_key or os.getenv("CEREVOX_API_KEY")
        if not self.api_key:
            raise ValueError("api_key is required for authentication")

        # Validate base_url format
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string")

        # Basic URL validation
        if not (base_url.startswith(HTTP) or base_url.startswith(HTTPS)):
            raise ValueError(f"base_url must start with {HTTP} or {HTTPS}")

        self.base_url = base_url.rstrip("/")  # Remove trailing slash

        # Set auth_url - defaults to base_url if not provided
        if auth_url:
            # Validate auth_url format
            if not auth_url or not isinstance(auth_url, str):
                raise ValueError("auth_url must be a non-empty string")
            if not (auth_url.startswith(HTTP) or auth_url.startswith(HTTPS)):
                raise ValueError(f"auth_url must start with {HTTP} or {HTTPS}")
            self.auth_url = auth_url.rstrip("/")
        else:
            self.auth_url = self.base_url

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
            files: Files to upload (for multipart requests)
            is_auth: If True, use auth_url and skip token validation (for auth endpoints)
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the API

        Raises:
            LexaAuthError: If authentication fails
            LexaError: If the request fails for other reasons
            LexaTimeoutError: If the request times out
            Various other LexaError subclasses: Based on response status and content
        """
        base_url = self.auth_url

        # Check if token needs refresh before making request
        if not is_auth:
            self._ensure_valid_token()
            base_url = self.base_url

        url = f"{base_url}{endpoint}"

        # Merge additional headers
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=request_headers,
                files=files,
                timeout=self.timeout,
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
        """Close the HTTP session"""
        if hasattr(self, "session"):
            self.session.close()

    def __enter__(self) -> "BaseClient":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit"""
        self.close()

    # Token Management Methods

    def _ensure_valid_token(self) -> None:
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
                self._refresh_token(self.refresh_token)
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
        self.session.headers.update(
            {"Authorization": f"Bearer {token_response.access_token}"}
        )

    # Authentication Methods

    def _login(self, api_key: str) -> TokenResponse:
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

        # Skip token validation for login request and use auth_url
        response_data = self._request(
            "POST", "/token/login", headers=headers, is_auth=True
        )

        token_response = TokenResponse(**response_data)

        # Store all token information
        self._store_token_info(token_response)

        return token_response

    def _refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: The refresh token

        Returns:
            TokenResponse with new tokens
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
        Revoke the current access token

        Returns:
            MessageResponse with revocation confirmation
        """
        response_data = self._request("POST", "/token/revoke", is_auth=True)

        # Clear all token information since the token is now revoked
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

        # Remove the authorization header
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]

        return MessageResponse(**response_data)
