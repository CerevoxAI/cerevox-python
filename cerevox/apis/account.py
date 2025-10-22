"""
Cerevox SDK's Synchronous Account Client
"""

import logging
from typing import Any, Dict, List, Optional

from ..core import (
    AccountInfo,
    AccountPlan,
    Client,
    CreatedResponse,
    DeletedResponse,
    InsufficientPermissionsError,
    LexaAuthError,
    UpdatedResponse,
    UsageMetrics,
    User,
    UserCreate,
    UserDelete,
    UserUpdate,
)

logger = logging.getLogger(__name__)


class Account(Client):
    """
    Official Synchronous Python Client for Cerevox Account Management.

    This client provides a clean, Pythonic interface to the Cerevox Account API,
    supporting comprehensive account management and user administration operations.

    Examples
    --------
    Basic client initialization and usage:

    >>> client = Account(api_key="your_pat_token")
    >>> account = client.get_account_info()
    >>> print(f"Account: {account.account_name}")

    User management operations:

    >>> users = client.get_users()
    >>> print(f"Found {len(users)} users")
    >>> new_user = client.create_user(
    ...     email="newuser@company.com",
    ...     name="New User"
    ... )

    Error handling:

    >>> try:
    ...     user = client.get_user_by_id("user123")
    ... except InsufficientPermissionsError:
    ...     print("Admin permissions required")

    Notes
    -----
    This client is thread-safe and can be used across multiple threads.
    Authentication is automatically handled during initialization and
    tokens are refreshed as needed.

    All methods that require admin permissions will raise
    InsufficientPermissionsError if the current user lacks the
    necessary privileges.

    Happy Managing! 👥 ✨
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        data_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        max_retries: int = 3,
        session_kwargs: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Account client and authenticate with Cerevox.

        Parameters
        ----------
        api_key : str, optional
            User Personal Access Token (PAT) for authentication. If None,
            attempts to read from CEREVOX_API_KEY environment variable.
        data_url : str, optional
            Base URL for the Cerevox Account API. Uses default production
            endpoint if not specified.
        auth_url : str, optional
            Base URL for authentication endpoints. Inherits from data_url
            if not provided.
        max_retries : int, default 3
            Maximum retry attempts for transient failures. Must be >= 0.
        session_kwargs : dict, optional
            Additional configuration for the requests.Session instance,
            such as proxies, verify, or cert parameters.
        timeout : float, default 30.0
            Default timeout for all requests in seconds. Individual methods
            may override this value.
        **kwargs : dict
            Additional keyword arguments passed to the parent Client class.

        Raises
        ------
        LexaAuthError
            If authentication fails due to invalid credentials or
            network connectivity issues.

        Notes
        -----
        Authentication occurs automatically during initialization. The client
        will validate the provided API key and establish a session with
        the Cerevox API servers.
        """
        # For Account class, if no URLs are provided, use the default base_url for both
        # If data_url is not provided, use auth_url or default base_url
        default_url = "https://dev.cerevox.ai/v1"

        data_url = data_url or auth_url or default_url
        auth_url = auth_url or data_url or default_url
        base_url = data_url

        super().__init__(
            api_key=api_key,
            base_url=base_url,
            auth_url=auth_url,
            data_url=data_url,
            max_retries=max_retries,
            session_kwargs=session_kwargs,
            timeout=timeout,
            **kwargs,
        )

    # Account Management Methods

    def get_account_info(self) -> AccountInfo:
        """
        Retrieve current account information and metadata.

        Returns
        -------
        AccountInfo
            Object containing account_id, account_name, and other
            account metadata such as creation date and status.
        """
        response_data = self._request("GET", "/accounts/my")
        return AccountInfo(**response_data)

    def get_account_plan(self, account_id: str) -> AccountPlan:
        """
        Retrieve account plan information and usage limits.

        Parameters
        ----------
        account_id : str
            The unique account identifier. Must be a valid UUID string.

        Returns
        -------
        AccountPlan
            Object containing plan type, limits, features, and billing
            information for the specified account
        """
        response_data = self._request("GET", f"/accounts/{account_id}/plan")
        return AccountPlan(**response_data["plan"])

    def get_account_usage(self, account_id: str) -> UsageMetrics:
        """
        Retrieve current usage metrics for the account.

        Parameters
        ----------
        account_id : str
            The unique account identifier. Must be a valid UUID string.

        Returns
        -------
        UsageMetrics
            Object containing current usage statistics including API calls,
            storage utilization, user count, and other relevant metrics.
        """
        response_data = self._request("GET", f"/accounts/{account_id}/usage")
        return UsageMetrics(**response_data)

    # User Management Methods

    def create_user(self, email: str, name: str) -> CreatedResponse:
        """
        Create a new user in the current account.

        Parameters
        ----------
        email : str
            Valid email address for the new user. Must be unique within
            the account and follow standard email format validation.
        name : str
            Display name for the user. Cannot be empty and should be
            between 1-100 characters in length.

        Returns
        -------
        CreatedResponse
            Object containing the creation status, user ID, and any
            relevant metadata about the newly created user.

        Raises
        ------
        InsufficientPermissionsError
            If the current user does not have admin privileges required
            to create new users.

        Notes
        -----
        Only users with admin privileges can create new users. The newly
        created user will receive an invitation email with setup instructions.
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
        Retrieve all users in the current account.

        Returns
        -------
        List[User]
            List of User objects containing user information such as
            user_id, email, name, role, and account status.

        Notes
        -----
        This method returns all users regardless of their status (active,
        pending, suspended). Use the status field to filter as needed.
        """
        response_data = self._request("GET", "/users")
        if isinstance(response_data, list):
            return [User(**user_data) for user_data in response_data]
        # Handle case where response is wrapped
        users_data = response_data.get("users", response_data)
        return [User(**user_data) for user_data in users_data]

    def get_user_me(self) -> User:
        """
        Retrieve information about the currently authenticated user.

        Returns
        -------
        User
            User object containing the current user's profile information
            including user_id, email, name, role, and account permissions.
        """
        response_data = self._request("GET", "/users/me")
        return User(**response_data)

    def update_user_me(self, name: str) -> UpdatedResponse:
        """
        Update the current user's profile information.

        Parameters
        ----------
        name : str
            New display name for the current user. Must be between
            1-100 characters and cannot be empty.

        Returns
        -------
        UpdatedResponse
            Object containing the update status and any relevant
            metadata about the profile changes.

        Notes
        -----
        Users can only update their own profile information. To update
        other users, use update_user_by_id() with admin privileges.
        """
        request = UserUpdate(name=name)
        response_data = self._request(
            "PUT", "/users/me", json_data=request.model_dump()
        )
        return UpdatedResponse(**response_data)

    def get_user_by_id(self, user_id: str) -> User:
        """
        Retrieve user information by user ID (Admin only).

        Parameters
        ----------
        user_id : str
            The unique user identifier. Must be a valid UUID string.

        Returns
        -------
        User
            User object containing complete profile information for
            the specified user including email, name, role, and status.

        Raises
        ------
        InsufficientPermissionsError
            If the current user does not have admin privileges.
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
        Update user information by user ID (Admin only).

        Parameters
        ----------
        user_id : str
            The unique user identifier. Must be a valid UUID string.
        name : str
            New display name for the user. Must be between 1-100
            characters and cannot be empty.

        Returns
        -------
        UpdatedResponse
            Object containing the update status and any relevant
            metadata about the profile changes.

        Raises
        ------
        InsufficientPermissionsError
            If the current user does not have admin privileges.
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
        Delete a user by ID with email confirmation (Admin only).

        Parameters
        ----------
        user_id : str
            The unique user identifier. Must be a valid UUID string.
        email : str
            Email address of the user being deleted, required for
            confirmation and audit purposes.

        Returns
        -------
        DeletedResponse
            Object containing the deletion status and any relevant
            metadata about the operation.

        Raises
        ------
        InsufficientPermissionsError
            If the current user does not have admin privileges.

        Notes
        -----
        This is a destructive operation that cannot be undone. The email
        parameter serves as a confirmation mechanism to prevent accidental
        deletions. All user data and associated resources will be permanently
        removed. Comprehensive audit logs are maintained for compliance.

        Users cannot delete themselves using this method. Active sessions
        for the deleted user will be immediately invalidated.
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
