"""
Cerevox SDK's Synchronous Account Client
"""

import logging
from typing import Any, Dict, List, Optional

from ..core.base_client import BaseClient
from ..core.exceptions import (
    InsufficientPermissionsError,
    LexaAuthError,
)
from ..core.models import (
    AccountInfo,
    AccountPlan,
    CreatedResponse,
    DeletedResponse,
    UpdatedResponse,
    UsageMetrics,
    User,
    UserCreate,
    UserDelete,
    UserUpdate,
)

logger = logging.getLogger(__name__)


class Account(BaseClient):
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
        super().__init__(
            email=email,
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            session_kwargs=session_kwargs,
            timeout=timeout,
            **kwargs,
        )

    # Authentication Methods (inherited from BaseClient)

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
