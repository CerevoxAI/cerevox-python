"""
Test suite for cerevox.apis.async_account

Comprehensive tests to achieve 100% code coverage for the AsyncAccount class,
including all methods, error handling, and edge cases.
"""

import asyncio
import os
from unittest.mock import patch

import aiohttp
import pytest
from aioresponses import aioresponses

from cerevox import AsyncAccount
from cerevox.core import (
    AccountInfo,
    AccountPlan,
    CreatedResponse,
    DeletedResponse,
    InsufficientPermissionsError,
    LexaAuthError,
    LexaError,
    LexaRateLimitError,
    LexaTimeoutError,
    LexaValidationError,
    MessageResponse,
    TokenResponse,
    UpdatedResponse,
    UsageMetrics,
    User,
)


@pytest.fixture
def mock_login_response():
    """Standard login response for mocking"""
    return {
        "access_token": "test-access-token",
        "expires_in": 3600,
        "refresh_token": "test-refresh-token",
        "token_type": "Bearer",
    }


def setup_login_mock(mock, login_response=None):
    """Helper to setup the standard login mock that happens during client initialization"""
    if login_response is None:
        login_response = {
            "access_token": "test-access-token",
            "expires_in": 3600,
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
        }

    mock.post(
        "https://dev.cerevox.ai/v1/token/login",
        payload=login_response,
        status=200,
    )


class TestAsyncAccountInitialization:
    """Test AsyncAccount client initialization"""

    def setup_method(self):
        """Set up test fixtures with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during client initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    def test_init_with_api_key(self):
        """Test initialization with API key parameter"""
        client = AsyncAccount(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.data_url == "https://dev.cerevox.ai/v1"
        assert client.timeout.total == 30.0
        assert client.max_retries == 3

    def test_init_without_api_key(self):
        """Test initialization without API key raises error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="api_key is required for authentication",
            ):
                AsyncAccount()

    def test_init_with_env_var(self):
        """Test initialization with environment variable"""
        with patch.dict(os.environ, {"CEREVOX_API_KEY": "env-api-key"}):
            client = AsyncAccount(api_key=None)
            assert client.api_key == "env-api-key"

    def test_init_with_custom_data_url(self):
        """Test initialization with custom base URL"""
        client = AsyncAccount(
            api_key="test-key",
            data_url="https://custom.api.com",
        )
        assert client.data_url == "https://custom.api.com"

    def test_init_invalid_data_url(self):
        """Test initialization with invalid base URL"""
        with pytest.raises(ValueError, match="(data_url|base_url) must start with"):
            AsyncAccount(api_key="test-key", data_url="invalid-url")

    def test_init_invalid_max_retries(self):
        """Test initialization with invalid max_retries"""
        with pytest.raises(TypeError, match="max_retries must be an integer"):
            AsyncAccount(api_key="test-key", max_retries="invalid")

        with pytest.raises(
            ValueError, match="max_retries must be a non-negative integer"
        ):
            AsyncAccount(api_key="test-key", max_retries=-1)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with AsyncAccount(api_key="test-key") as client:
            assert client.api_key == "test-key"
            assert client.session is not None

    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        """Test session start and close lifecycle"""
        client = AsyncAccount(api_key="test-key")

        # Session should be None initially
        assert client.session is None

        await client.start_session()
        assert client.session is not None

        await client.close_session()
        assert client.session is None


class TestAsyncAccountAuthentication:
    """Test AsyncAccount authentication methods"""

    def setup_method(self):
        """Set up test fixtures with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during client initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login"""
        # Mock the specific login call for this test
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/login",
            payload={
                "access_token": "access_123",
                "expires_in": 3600,
                "refresh_token": "refresh_456",
                "token_type": "Bearer",
            },
            status=200,
            headers={"x-request-id": "req-123"},
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client._login("test-api-key")

            assert isinstance(result, TokenResponse)
            assert result.access_token == "access_123"
            assert result.expires_in == 3600
            assert result.refresh_token == "refresh_456"
            assert result.token_type == "Bearer"

    @pytest.mark.asyncio
    async def test_login_failure(self):
        """Test login failure"""
        # Mock the failing login call
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/login",
            payload={"error": "Invalid credentials"},
            status=401,
            headers={"x-request-id": "req-123"},
        )

        async with AsyncAccount(api_key="test-key") as client:
            with pytest.raises(LexaAuthError):
                await client._login("wrong-api-key")

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/refresh",
            payload={
                "access_token": "new_access_123",
                "expires_in": 3600,
                "refresh_token": "new_refresh_456",
                "token_type": "Bearer",
            },
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client._refresh_token("refresh_456")

            assert isinstance(result, TokenResponse)
            assert result.access_token == "new_access_123"

    @pytest.mark.asyncio
    async def test_revoke_token_success(self):
        """Test successful token revocation"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/revoke",
            payload={"message": "Token revoked successfully", "status": "success"},
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client._revoke_token()

            assert isinstance(result, MessageResponse)
            assert result.message == "Token revoked successfully"
            assert result.status == "success"


class TestAsyncAccountManagement:
    """Test AsyncAccount management methods"""

    def setup_method(self):
        """Set up test fixtures with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during client initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_get_account_info_success(self):
        """Test successful account info retrieval"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/accounts/my",
            payload={
                "account_id": "acc-123",
                "account_name": "Test Account",
            },
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.get_account_info()

            assert isinstance(result, AccountInfo)
            assert result.account_id == "acc-123"
            assert result.account_name == "Test Account"

    @pytest.mark.asyncio
    async def test_get_account_plan_success(self):
        """Test successful account plan retrieval"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/accounts/acc-123/plan",
            payload={
                "plan": {
                    "plan": "professional",
                    "base": 1000,
                    "bytes": 1073741824,
                    "messages": 10000,
                    "status": "active",
                }
            },
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.get_account_plan("acc-123")

            assert isinstance(result, AccountPlan)
            assert result.plan == "professional"
            assert result.base == 1000
            assert result.bytes == 1073741824
            assert result.status == "active"

    @pytest.mark.asyncio
    async def test_get_account_usage_success(self):
        """Test successful account usage retrieval"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/accounts/acc-123/usage",
            payload={
                "files": {"processed": 50, "total": 100},
                "pages": {"processed": 500, "total": 1000},
                "advanced_pages": {"processed": 25, "total": 50},
                "storage": {"used": 524288000, "total": 1073741824},
            },
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.get_account_usage("acc-123")

            assert isinstance(result, UsageMetrics)
            assert result.files["processed"] == 50
            assert result.pages["processed"] == 500
            assert result.storage["used"] == 524288000


class TestAsyncUserManagement:
    """Test AsyncAccount user management methods"""

    def setup_method(self):
        """Set up test fixtures with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during client initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/users",
            payload={"created": True, "status": "success"},
            status=201,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.create_user("new@example.com", "New User")

            assert isinstance(result, CreatedResponse)
            assert result.created is True
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_create_user_insufficient_permissions(self):
        """Test user creation with insufficient permissions"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/users",
            payload={"error": "Forbidden"},
            status=403,
        )

        async with AsyncAccount(api_key="test-key") as client:
            with pytest.raises(InsufficientPermissionsError):
                await client.create_user("new@example.com", "New User")

    @pytest.mark.asyncio
    async def test_get_users_success(self):
        """Test successful users retrieval"""
        user_data = [
            {
                "user_id": "user-1",
                "email": "user1@example.com",
                "name": "User One",
                "account_id": "acc-123",
                "isadmin": True,
                "isbanned": False,
            },
            {
                "user_id": "user-2",
                "email": "user2@example.com",
                "name": "User Two",
                "account_id": "acc-123",
                "isadmin": False,
                "isbanned": False,
            },
        ]

        self.mock.get(
            "https://dev.cerevox.ai/v1/users",
            payload=user_data,
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.get_users()

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(user, User) for user in result)
            assert result[0].user_id == "user-1"
            assert result[0].isadmin is True

    @pytest.mark.asyncio
    async def test_get_users_wrapped_response(self):
        """Test users retrieval with wrapped response"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/users",
            payload={
                "users": [
                    {
                        "user_id": "user-1",
                        "email": "user1@example.com",
                        "name": "User One",
                        "account_id": "acc-123",
                        "isadmin": True,
                        "isbanned": False,
                    }
                ]
            },
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.get_users()

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].user_id == "user-1"

    @pytest.mark.asyncio
    async def test_get_user_me_success(self):
        """Test successful current user retrieval"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/users/me",
            payload={
                "user_id": "user-123",
                "email": "me@example.com",
                "name": "Current User",
                "account_id": "acc-123",
                "isadmin": True,
                "isbanned": False,
            },
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.get_user_me()

            assert isinstance(result, User)
            assert result.user_id == "user-123"
            assert result.email == "me@example.com"
            assert result.isadmin is True

    @pytest.mark.asyncio
    async def test_update_user_me_success(self):
        """Test successful current user update"""
        self.mock.put(
            "https://dev.cerevox.ai/v1/users/me",
            payload={"updated": True, "status": "success"},
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.update_user_me("Updated Name")

            assert isinstance(result, UpdatedResponse)
            assert result.updated is True
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self):
        """Test successful user retrieval by ID"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={
                "user_id": "user-456",
                "email": "other@example.com",
                "name": "Other User",
                "account_id": "acc-123",
                "isadmin": False,
                "isbanned": False,
            },
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.get_user_by_id("user-456")

            assert isinstance(result, User)
            assert result.user_id == "user-456"
            assert result.email == "other@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_insufficient_permissions(self):
        """Test user retrieval by ID with insufficient permissions"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={"error": "Forbidden"},
            status=403,
        )

        async with AsyncAccount(api_key="test-key") as client:
            with pytest.raises(InsufficientPermissionsError):
                await client.get_user_by_id("user-456")

    @pytest.mark.asyncio
    async def test_update_user_by_id_success(self):
        """Test successful user update by ID"""
        self.mock.put(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={"updated": True, "status": "success"},
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.update_user_by_id("user-456", "New Name")

            assert isinstance(result, UpdatedResponse)
            assert result.updated is True

    @pytest.mark.asyncio
    async def test_delete_user_by_id_success(self):
        """Test successful user deletion by ID"""
        self.mock.delete(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={"deleted": True, "status": "success"},
            status=200,
        )

        async with AsyncAccount(api_key="test-key") as client:
            result = await client.delete_user_by_id("user-456", "confirm@example.com")

            assert isinstance(result, DeletedResponse)
            assert result.deleted is True


class TestAsyncAccountErrorHandling:
    """Test AsyncAccount error handling"""

    def setup_method(self):
        """Set up test fixtures with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during client initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test request timeout handling"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/accounts/my",
            exception=asyncio.TimeoutError(),
        )

        async with AsyncAccount(api_key="test-key") as client:
            with pytest.raises(LexaTimeoutError):
                await client.get_account_info()

    @pytest.mark.asyncio
    async def test_client_error(self):
        """Test aiohttp client error handling"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/accounts/my",
            exception=aiohttp.ClientError("Connection failed"),
        )

        async with AsyncAccount(api_key="test-key") as client:
            with pytest.raises(LexaError):
                await client.get_account_info()

    @pytest.mark.asyncio
    async def test_rate_limit_error(self):
        """Test rate limit error handling"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/accounts/my",
            payload={"error": "Rate limit exceeded", "retry_after": 60},
            status=429,
            headers={"x-request-id": "req-123"},
        )

        async with AsyncAccount(api_key="test-key") as client:
            with pytest.raises(LexaRateLimitError) as exc_info:
                await client.get_account_info()

            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_validation_error(self):
        """Test validation error handling"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/users",
            payload={
                "error": "Validation failed",
                "validation_errors": {"email": "Invalid email format"},
            },
            status=400,
        )

        async with AsyncAccount(api_key="test-key") as client:
            with pytest.raises(LexaValidationError) as exc_info:
                await client.create_user("invalid-email", "Test User")

            assert "email" in exc_info.value.validation_errors

    @pytest.mark.asyncio
    async def test_non_json_response(self):
        """Test handling of non-JSON responses"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/users/me",  # Use an endpoint that doesn't parse to a specific model
            body="Server maintenance",
            status=200,
            content_type="text/plain",
        )

        async with AsyncAccount(api_key="test-key") as client:
            # Use the _request method directly to test non-JSON handling
            result = await client._request("GET", "/users/me")
            # Should return basic success response for non-JSON 200 responses
            assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_failed_request_id_extraction(self):
        """Test handling when request ID extraction fails"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/accounts/my",
            payload={"error": "Server error"},
            status=500,
            # No x-request-id header
        )

        async with AsyncAccount(api_key="test-key") as client:
            with pytest.raises(LexaError) as exc_info:
                await client.get_account_info()

            # Should use fallback request ID
            assert exc_info.value.request_id == "Failed to get request ID from response"

    @pytest.mark.asyncio
    async def test_auto_session_start(self):
        """Test automatic session start when making requests"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/accounts/my",
            payload={"account_id": "acc-123", "account_name": "Test"},
            status=200,
        )

        client = AsyncAccount(api_key="test-key")
        # Don't use context manager to test auto-start
        assert client.session is None

        result = await client.get_account_info()
        assert client.session is not None
        assert result.account_id == "acc-123"

        await client.close_session()


class TestAsyncAccountSessionManagement:
    """Test AsyncAccount session management"""

    def setup_method(self):
        """Set up test fixtures with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during client initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_close_session_when_none(self):
        """Test closing session when it's None"""
        client = AsyncAccount(api_key="test-key")
        assert client.session is None
        # Should not raise an error
        await client.close_session()
        assert client.session is None

    @pytest.mark.asyncio
    async def test_multiple_session_starts(self):
        """Test multiple session start calls"""
        client = AsyncAccount(api_key="test-key")

        await client.start_session()
        session1 = client.session

        # Starting again should not create a new session
        await client.start_session()
        session2 = client.session

        assert session1 is session2

        await client.close_session()


class TestAsyncAccountFullCoverage:

    def setup_method(self):
        """Set up test fixtures with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during client initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_bad_json_response(self):
        """Test that bad JSON response is handled"""
        # Mock a response with error status and non-JSON content
        self.mock.get(
            "https://dev.cerevox.ai/v1/test",
            body="Internal Server Error",  # Non-JSON content to trigger ValueError
            status=400,
            content_type="text/plain",
        )

        client = AsyncAccount(api_key="test-key")
        await client.start_session()
        # Should raise LexaValidationError with error data
        with pytest.raises(LexaValidationError) as exc_info:
            await client._request("GET", "/test")

        # Verify the error contains the expected data structure
        error = exc_info.value
        assert error.status_code == 400
        assert error.response_data["error"] == "HTTP 400"
        assert error.response_data["message"] == "Internal Server Error"
        await client.close_session()

    @pytest.mark.asyncio
    async def test_trigger_raise_in_create_user(self):
        """Test that create_user re-raises LexaAuthError when status code is not 403 (line 357)"""
        # Mock a 401 Unauthorized response to trigger LexaAuthError (not 403)
        self.mock.post(
            "https://dev.cerevox.ai/v1/users",
            payload={
                "error": "Invalid API key",
                "message": "Authentication failed",
            },
            status=401,
        )

        client = AsyncAccount(api_key="test-key")
        await client.start_session()
        # This should trigger the LexaAuthError with 401 status, which will hit line 357
        # (the raise statement that re-raises when status_code != 403)
        with pytest.raises(LexaAuthError) as exc_info:
            await client.create_user("test@example.com", "Test User")

        # Verify it's the original LexaAuthError being re-raised
        error = exc_info.value
        assert error.status_code == 401
        assert "Invalid API key" in error.message
        await client.close_session()

    @pytest.mark.asyncio
    async def test_trigger_raise_in_get_user_by_id(self):
        """Test that get_user_by_id re-raises LexaAuthError when status code is not 403 (line 357)"""
        # Mock a 401 Unauthorized response to trigger LexaAuthError (not 403)
        self.mock.get(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={
                "error": "Invalid API key",
                "message": "Authentication failed",
            },
            status=401,
        )

        client = AsyncAccount(api_key="test-key")
        await client.start_session()
        # This should trigger the LexaAuthError with 401 status, which will hit line 357
        # (the raise statement that re-raises when status_code != 403)
        with pytest.raises(LexaAuthError) as exc_info:
            await client.get_user_by_id("user-456")
            # Verify it's the original LexaAuthError being re-raised
            error = exc_info.value
            assert error.status_code == 401
            assert "Invalid API key" in error.message

        await client.close_session()

    @pytest.mark.asyncio
    async def test_trigger_raise_in_update_user_by_id(self):
        """Test that update_user_by_id re-raises LexaAuthError when status code is not 403 (line 357)"""
        # Mock a 401 Unauthorized response to trigger LexaAuthError (not 403)
        self.mock.put(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={
                "error": "Invalid API key",
                "message": "Authentication failed",
            },
            status=401,
        )

        client = AsyncAccount(api_key="test-key")
        await client.start_session()
        with pytest.raises(LexaAuthError) as exc_info:
            await client.update_user_by_id("user-456", "New Name")

            # Verify it's the original LexaAuthError being re-raised
            error = exc_info.value
            assert error.status_code == 401
            assert "Invalid API key" in error.message

        await client.close_session()

    @pytest.mark.asyncio
    async def test_trigger_raise_in_update_user_by_id_403(self):
        # Trigger 403 Forbidden
        self.mock.put(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={"error": "Forbidden", "message": "Authentication failed"},
            status=403,
        )

        client = AsyncAccount(api_key="test-key")
        await client.start_session()
        with pytest.raises(InsufficientPermissionsError) as exc_info:
            await client.update_user_by_id("user-456", "New Name")

            # Verify it's the original InsufficientPermissionsError being raised
            error = exc_info.value
            assert error.status_code == 403
            assert "Forbidden" in error.message
        await client.close_session()

    @pytest.mark.asyncio
    async def test_trigger_raise_in_delete_user_by_id(self):
        """Test that delete_user_by_id re-raises LexaAuthError when status code is not 403 (line 357)"""
        # Mock a 401 Unauthorized response to trigger LexaAuthError (not 403)
        self.mock.delete(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={
                "error": "Invalid API key",
                "message": "Authentication failed",
            },
            status=401,
        )

        client = AsyncAccount(api_key="test-key")
        await client.start_session()
        with pytest.raises(LexaAuthError) as exc_info:
            await client.delete_user_by_id("user-456", "confirm@example.com")

            # Verify it's the original LexaAuthError being re-raised
            error = exc_info.value
            assert error.status_code == 401
            assert "Invalid API key" in error.message

        await client.close_session()

    @pytest.mark.asyncio
    async def test_trigger_raise_in_delete_user_by_id_403(self):
        # Trigger 403 Forbidden
        self.mock.delete(
            "https://dev.cerevox.ai/v1/users/user-456",
            payload={"error": "Forbidden", "message": "Authentication failed"},
            status=403,
        )

        client = AsyncAccount(api_key="test-key")
        await client.start_session()
        with pytest.raises(InsufficientPermissionsError) as exc_info:
            await client.delete_user_by_id("user-456", "confirm@example.com")

            # Verify it's the original InsufficientPermissionsError being raised
            error = exc_info.value
            assert error.status_code == 403
            assert "Forbidden" in error.message

        await client.close_session()
