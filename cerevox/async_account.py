"""
Cerevox SDK's Asynchronous Account Client
"""

import asyncio
import base64
import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp

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

FAILED_ID = "Failed to get request ID from response"

logger = logging.getLogger(__name__)


class AsyncAccount:
    """
    Official Asynchronous Python Client for Cerevox Account Management

    This client provides a clean, Pythonic async interface to the Cerevox Account API,
    supporting user authentication, account management, and user administration.

    Example:
        >>> async with AsyncAccount(api_key="your-api-key") as client:
        ...     # Authenticate with email/password
        ...     tokens = await client.login("user@example.com", "password")
        ...     print(tokens.access_token)
        ...     # Get account information
        ...     account = await client.get_account_info()
        ...     print(account.account_name)
        ...     # Manage users
        ...     users = await client.get_users()
        ...     print(f"Found {len(users)} users")

    Happy Managing! 👥 ✨
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
        Initialize the AsyncAccount client

        Args:
            api_key: Your Cerevox API key. If not provided, will try CEREVOX_API_KEY
            base_url: Base URL for the Cerevox Account API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            **kwargs: Additional aiohttp ClientSession arguments
        """
        self.api_key = api_key or os.getenv("CEREVOX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it via "
                + "api_key parameter or CEREVOX_API_KEY environment variable."
            )

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
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "cerevox-python-async/0.1.6",
                "Content-Type": "application/json",
            },
            **kwargs,
        }

        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "AsyncAccount":
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

    async def login(self, email: str, password: str) -> TokenResponse:
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

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        response_data = await self._request("POST", "/token/login", headers=headers)
        return TokenResponse(**response_data)

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
        return TokenResponse(**response_data)

    async def revoke_token(self) -> MessageResponse:
        """
        Revoke the current access token

        Returns:
            MessageResponse with revocation confirmation
        """
        response_data = await self._request("POST", "/token/revoke")
        return MessageResponse(**response_data)

    # Account Management Methods

    async def get_account_info(self) -> AccountInfo:
        """
        Get current account information

        Returns:
            AccountInfo with account_id and account_name
        """
        response_data = await self._request("GET", "/accounts/my")
        return AccountInfo(**response_data)

    async def get_account_plan(self, account_id: str) -> AccountPlan:
        """
        Get account plan and limits information

        Args:
            account_id: The account identifier

        Returns:
            AccountPlan with plan details and limits
        """
        response_data = await self._request("GET", f"/accounts/{account_id}/plan")
        return AccountPlan(**response_data)

    async def get_account_usage(self, account_id: str) -> UsageMetrics:
        """
        Get account usage metrics

        Args:
            account_id: The account identifier

        Returns:
            UsageMetrics with current usage statistics
        """
        response_data = await self._request("GET", f"/accounts/{account_id}/usage")
        return UsageMetrics(**response_data)

    # User Management Methods

    async def create_user(self, email: str, name: str) -> CreatedResponse:
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
            response_data = await self._request(
                "POST", "/users", json_data=request.model_dump()
            )
            return CreatedResponse(**response_data)
        except LexaAuthError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(
                    "Admin permissions required to create users"
                ) from e
            raise

    async def get_users(self) -> List[User]:
        """
        Get list of all users in the account

        Returns:
            List of User objects
        """
        response_data = await self._request("GET", "/users")
        if isinstance(response_data, list):
            return [User(**user_data) for user_data in response_data]
        # Handle case where response is wrapped
        users_data = response_data.get("users", response_data)
        return [User(**user_data) for user_data in users_data]

    async def get_user_me(self) -> User:
        """
        Get current user information

        Returns:
            User object with current user details
        """
        response_data = await self._request("GET", "/users/me")
        return User(**response_data)

    async def update_user_me(self, name: str) -> UpdatedResponse:
        """
        Update current user information

        Args:
            name: Updated user display name

        Returns:
            UpdatedResponse with update status
        """
        request = UserUpdate(name=name)
        response_data = await self._request(
            "PUT", "/users/me", json_data=request.model_dump()
        )
        return UpdatedResponse(**response_data)

    async def get_user_by_id(self, user_id: str) -> User:
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
            response_data = await self._request("GET", f"/users/{user_id}")
            return User(**response_data)
        except LexaAuthError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(
                    "Admin permissions required to get user by ID"
                ) from e
            raise

    async def update_user_by_id(self, user_id: str, name: str) -> UpdatedResponse:
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
            response_data = await self._request(
                "PUT", f"/users/{user_id}", json_data=request.model_dump()
            )
            return UpdatedResponse(**response_data)
        except LexaAuthError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(
                    "Admin permissions required to update user by ID"
                ) from e
            raise

    async def delete_user_by_id(self, user_id: str, email: str) -> DeletedResponse:
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
            response_data = await self._request(
                "DELETE", f"/users/{user_id}", json_data=request.model_dump()
            )
            return DeletedResponse(**response_data)
        except LexaAuthError as e:
            if e.status_code == 403:
                raise InsufficientPermissionsError(
                    "Admin permissions required to delete user by ID"
                ) from e
            raise
