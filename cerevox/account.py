"""
Cerevox SDK's Synchronous Account Client
"""

import base64
import logging
import os
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    InsufficientPermissionsError,
    LexaAuthError,
    LexaError,
    LexaTimeoutError,
    create_error_from_response,
)
from .models import (
    AccountInfo,
    AccountPlan,
    CreatedResponse,
    DeletedResponse,
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
    UpdatedResponse,
    UsageMetrics,
    User,
    UserCreate,
    UserDelete,
    UserUpdate,
)

HTTP = "http://"
HTTPS = "https://"
FAILED_ID = "Failed to get request ID from response"

logger = logging.getLogger(__name__)


class Account:
    """
    Official Synchronous Python Client for Cerevox Account Management

    This client provides a clean, Pythonic interface to the Cerevox Account API,
    supporting user authentication, account management, and user administration.

    Example:
        >>> client = Account(email="user@example.com", api_key="password")
        >>> # Client automatically authenticates during initialization
        >>> # Get account information
        >>> account = client.get_account_info()
        >>> print(account.account_name)
        >>> # Manage users
        >>> users = client.get_users()
        >>> print(f"Found {len(users)} users")

    Happy Managing! 👥 ✨
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
        Initialize the Account client and automatically authenticate

        Args:
            email: User email address for authentication
            api_key: User password for authentication
            base_url: Base URL for the Cerevox Account API
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
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        All requests to Account API are handled by this method

        Args:
            method: The HTTP method to use
            endpoint: The API endpoint to call
            json_data: JSON data to send in the request body
            params: Query parameters to send in the request
            headers: Additional headers to send with the request
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

    def __enter__(self) -> "Account":
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

    # Account Management Methods

    def get_account_info(self) -> AccountInfo:
        """
        Get current account information

        Returns:
            AccountInfo with account_id and account_name
        """
        response_data = self._request("GET", "/accounts/my")
        return AccountInfo(**response_data)

    def get_account_plan(self, account_id: str) -> AccountPlan:
        """
        Get account plan and limits information

        Args:
            account_id: The account identifier

        Returns:
            AccountPlan with plan details and limits
        """
        response_data = self._request("GET", f"/accounts/{account_id}/plan")
        return AccountPlan(**response_data["plan"])

    def get_account_usage(self, account_id: str) -> UsageMetrics:
        """
        Get account usage metrics

        Args:
            account_id: The account identifier

        Returns:
            UsageMetrics with current usage statistics
        """
        response_data = self._request("GET", f"/accounts/{account_id}/usage")
        return UsageMetrics(**response_data)

    # User Management Methods

    def create_user(self, email: str, name: str) -> CreatedResponse:
        """
        Create a new user in the account

        Args:
            email: User email address
            name: User display name

        Returns:
            CreatedResponse with creation status

        Raises:
            InsufficientPermissionsError: If not an admin user
        """
        request = UserCreate(email=email, name=name)
        try:
            response_data = self._request(
                "POST", "/users", json_data=request.model_dump()
            )
            return CreatedResponse(**response_data)
        except LexaAuthError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(
                    "Admin permissions required to create users"
                ) from e
            raise

    def get_users(self) -> List[User]:
        """
        Get list of all users in the account

        Returns:
            List of User objects
        """
        response_data = self._request("GET", "/users")
        if isinstance(response_data, list):
            return [User(**user_data) for user_data in response_data]
        # Handle case where response is wrapped
        users_data = response_data.get("users", response_data)
        return [User(**user_data) for user_data in users_data]

    def get_user_me(self) -> User:
        """
        Get current user information

        Returns:
            User object with current user details
        """
        response_data = self._request("GET", "/users/me")
        return User(**response_data)

    def update_user_me(self, name: str) -> UpdatedResponse:
        """
        Update current user information

        Args:
            name: Updated user display name

        Returns:
            UpdatedResponse with update status
        """
        request = UserUpdate(name=name)
        response_data = self._request(
            "PUT", "/users/me", json_data=request.model_dump()
        )
        return UpdatedResponse(**response_data)

    def get_user_by_id(self, user_id: str) -> User:
        """
        Get user information by ID (Admin only)

        Args:
            user_id: The user identifier

        Returns:
            User object with user details

        Raises:
            InsufficientPermissionsError: If not an admin user
        """
        try:
            response_data = self._request("GET", f"/users/{user_id}")
            return User(**response_data)
        except LexaAuthError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(
                    "Admin permissions required to get user by ID"
                ) from e
            raise

    def update_user_by_id(self, user_id: str, name: str) -> UpdatedResponse:
        """
        Update user information by ID (Admin only)

        Args:
            user_id: The user identifier
            name: Updated user display name

        Returns:
            UpdatedResponse with update status

        Raises:
            InsufficientPermissionsError: If not an admin user
        """
        request = UserUpdate(name=name)
        try:
            response_data = self._request(
                "PUT", f"/users/{user_id}", json_data=request.model_dump()
            )
            return UpdatedResponse(**response_data)
        except LexaAuthError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(
                    "Admin permissions required to update user by ID"
                ) from e
            raise

    def delete_user_by_id(self, user_id: str, email: str) -> DeletedResponse:
        """
        Delete user by ID (Admin only)

        Args:
            user_id: The user identifier
            email: Email confirmation for deletion

        Returns:
            DeletedResponse with deletion status

        Raises:
            InsufficientPermissionsError: If not an admin user
        """
        request = UserDelete(email=email)
        try:
            response_data = self._request(
                "DELETE", f"/users/{user_id}", json_data=request.model_dump()
            )
            return DeletedResponse(**response_data)
        except LexaAuthError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(
                    "Admin permissions required to delete user by ID"
                ) from e
            raise
