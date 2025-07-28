"""
Base classes for Cerevox SDK clients to reduce code duplication
"""

import base64
import logging
import os
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
    - Authentication (login, refresh_token, revoke_token)
    - Context manager support
    """

    def __init__(
        self,
        *,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://dev.cerevox.ai/v1",
        max_retries: int = 3,
        session_kwargs: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the base client

        Args:
            email: User email address for authentication
            api_key: User password for authentication
            base_url: Base URL for the Cerevox API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            session_kwargs: Additional arguments to pass to requests.Session
        """
        self.email = email
        self.api_key = api_key or os.getenv("CEREVOX_API_KEY")
        if not self.email or not self.api_key:
            raise ValueError("Both email and api_key are required for authentication")

        # Validate base_url format
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string")

        # Basic URL validation
        if not (base_url.startswith(HTTP) or base_url.startswith(HTTPS)):
            raise ValueError(f"base_url must start with {HTTP} or {HTTPS}")

        self.base_url = base_url.rstrip("/")  # Remove trailing slash
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

        # Automatically authenticate using email and password
        self.login(self.email, self.api_key)

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
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
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the API

        Raises:
            LexaAuthError: If authentication fails
            LexaError: If the request fails for other reasons
            LexaTimeoutError: If the request times out
            Various other LexaError subclasses: Based on response status and content
        """
        url = f"{self.base_url}{endpoint}"

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
            logger.error(f"Request timeout for {method} {url}: {e}")
            raise LexaTimeoutError(
                "Request timed out", timeout_duration=self.timeout
            ) from e

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {method} {url}: {e}")
            raise LexaError(f"Request failed: {e}", request_id=FAILED_ID) from e

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

    # Authentication Methods

    def login(self, email: str, password: str) -> TokenResponse:
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

        response_data = self._request("POST", "/token/login", headers=headers)

        token_response = TokenResponse(**response_data)

        self.session.headers.update(
            {"Authorization": f"Bearer {token_response.access_token}"}
        )

        return token_response

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: The refresh token

        Returns:
            TokenResponse with new tokens
        """
        request = TokenRefreshRequest(refresh_token=refresh_token)
        response_data = self._request(
            "POST", "/token/refresh", json_data=request.model_dump()
        )
        token_response = TokenResponse(**response_data)

        self.session.headers.update(
            {"Authorization": f"Bearer {token_response.access_token}"}
        )

        return token_response

    def revoke_token(self) -> MessageResponse:
        """
        Revoke the current access token

        Returns:
            MessageResponse with revocation confirmation
        """
        response_data = self._request("POST", "/token/revoke")

        # Remove the authorization header since the token is now revoked
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]

        return MessageResponse(**response_data)
