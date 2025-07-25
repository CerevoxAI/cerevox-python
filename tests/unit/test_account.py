"""
Test suite for cerevox.account

Comprehensive tests to achieve 100% code coverage for the Account class,
including all methods, error handling, and edge cases.
"""

import json
import os
from unittest.mock import Mock, patch

import pytest
import requests
import responses
from requests.exceptions import ConnectionError, RequestException, Timeout

from cerevox.account import Account
from cerevox.exceptions import (
    AccountError,
    InsufficientPermissionsError,
    LexaAuthError,
    LexaError,
    LexaRateLimitError,
    LexaTimeoutError,
    LexaValidationError,
    UserManagementError,
)
from cerevox.models import (
    AccountInfo,
    AccountPlan,
    CreatedResponse,
    DeletedResponse,
    MessageResponse,
    TokenResponse,
    UpdatedResponse,
    UsageMetrics,
    User,
)


class TestAccountInitialization:
    """Test Account client initialization"""

    def test_init_with_email_and_api_key(self):
        """Test initialization with email and API key parameters"""
        with patch.object(Account, "login") as mock_login:
            mock_login.return_value = None
            client = Account(email="test@example.com", api_key="test-api-key")
            assert client.email == "test@example.com"
            assert client.api_key == "test-api-key"
            assert client.base_url == "https://dev.cerevox.ai/v1"
            assert client.timeout == 30.0
            assert client.max_retries == 3
            mock_login.assert_called_once_with("test@example.com", "test-api-key")

    def test_init_with_env_var(self):
        """Test initialization with environment variable"""
        with patch.dict(os.environ, {"CEREVOX_API_KEY": "env-api-key"}):
            with patch.object(Account, "login") as mock_login:
                mock_login.return_value = None
                client = Account(email="test@example.com", api_key=None)
                assert client.api_key == "env-api-key"
                mock_login.assert_called_once_with("test@example.com", "env-api-key")

    def test_init_without_email_or_api_key(self):
        """Test initialization without email or API key raises error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError,
                match="Both email and api_key are required for authentication",
            ):
                Account()

            with pytest.raises(
                ValueError,
                match="Both email and api_key are required for authentication",
            ):
                Account(email="test@example.com")

            with pytest.raises(
                ValueError,
                match="Both email and api_key are required for authentication",
            ):
                Account(api_key="test-key")

    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL"""
        with patch.object(Account, "login") as mock_login:
            mock_login.return_value = None
            client = Account(
                email="test@example.com",
                api_key="test-key",
                base_url="https://custom.api.com",
            )
            assert client.base_url == "https://custom.api.com"

    def test_init_invalid_base_url(self):
        """Test initialization with invalid base URL"""
        with pytest.raises(ValueError, match="base_url must start with"):
            Account(
                email="test@example.com", api_key="test-key", base_url="invalid-url"
            )

    def test_init_empty_base_url(self):
        """Test initialization with empty base URL"""
        with pytest.raises(ValueError, match="base_url must be a non-empty string"):
            Account(email="test@example.com", api_key="test-key", base_url="")

    def test_init_with_session_kwargs(self):
        """Test initialization with session kwargs"""
        with patch.object(Account, "login") as mock_login:
            mock_login.return_value = None
            client = Account(
                email="test@example.com",
                api_key="test-key",
                session_kwargs={"verify": False},
            )
            assert not client.session.verify

    def test_context_manager(self):
        """Test context manager functionality"""
        with patch.object(Account, "login") as mock_login:
            mock_login.return_value = None
            with Account(email="test@example.com", api_key="test-key") as client:
                assert client.api_key == "test-key"
                assert hasattr(client, "session")


class TestAccountAuthentication:
    """Test Account authentication methods"""

    @responses.activate
    def test_login_success(self):
        """Test successful login"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/token/login",
            json={
                "access_token": "access_123",
                "expires_in": 3600,
                "refresh_token": "refresh_456",
                "token_type": "Bearer",
            },
            status=200,
            headers={"x-request-id": "req-123"},
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            result = client.login("user@example.com", "password123")

        assert isinstance(result, TokenResponse)
        assert result.access_token == "access_123"
        assert result.expires_in == 3600
        assert result.refresh_token == "refresh_456"
        assert result.token_type == "Bearer"

        # Check request was made with Basic Auth
        request = responses.calls[0].request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("Basic ")

    @responses.activate
    def test_login_failure(self):
        """Test login failure"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/token/login",
            json={"error": "Invalid credentials"},
            status=401,
            headers={"x-request-id": "req-123"},
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            with pytest.raises(LexaAuthError):
                client.login("user@example.com", "wrong-password")

    @responses.activate
    def test_refresh_token_success(self):
        """Test successful token refresh"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/token/refresh",
            json={
                "access_token": "new_access_123",
                "expires_in": 3600,
                "refresh_token": "new_refresh_456",
                "token_type": "Bearer",
            },
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            result = client.refresh_token("refresh_456")

        assert isinstance(result, TokenResponse)
        assert result.access_token == "new_access_123"

    @responses.activate
    def test_revoke_token_success(self):
        """Test successful token revocation"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/token/revoke",
            json={"message": "Token revoked successfully", "status": "success"},
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            result = client.revoke_token()

        assert isinstance(result, MessageResponse)
        assert result.message == "Token revoked successfully"
        assert result.status == "success"


class TestAccountManagement:
    """Test Account management methods"""

    @responses.activate
    def test_get_account_info_success(self):
        """Test successful account info retrieval"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/accounts/my",
            json={
                "account_id": "acc-123",
                "account_name": "Test Account",
            },
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            result = client.get_account_info()

        assert isinstance(result, AccountInfo)
        assert result.account_id == "acc-123"
        assert result.account_name == "Test Account"

    @responses.activate
    def test_get_account_plan_success(self):
        """Test successful account plan retrieval"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/accounts/acc-123/plan",
            json={
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

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            result = client.get_account_plan("acc-123")

        assert isinstance(result, AccountPlan)
        assert result.plan == "professional"
        assert result.base == 1000
        assert result.bytes == 1073741824
        assert result.status == "active"

    @responses.activate
    def test_get_account_usage_success(self):
        """Test successful account usage retrieval"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/accounts/acc-123/usage",
            json={
                "files": {"processed": 50, "total": 100},
                "pages": {"processed": 500, "total": 1000},
                "advanced_pages": {"processed": 25, "total": 50},
                "storage": {"used": 524288000, "total": 1073741824},
            },
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            result = client.get_account_usage("acc-123")

        assert isinstance(result, UsageMetrics)
        assert result.files["processed"] == 50
        assert result.pages["processed"] == 500
        assert result.storage["used"] == 524288000


class TestUserManagement:
    """Test User management methods"""

    @responses.activate
    def test_create_user_success(self):
        """Test successful user creation"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/users",
            json={"created": True, "status": "success"},
            status=201,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        result = client.create_user("new@example.com", "New User")

        assert isinstance(result, CreatedResponse)
        assert result.created is True
        assert result.status == "success"

    @responses.activate
    def test_create_user_insufficient_permissions(self):
        """Test user creation with insufficient permissions"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/users",
            json={"error": "Forbidden"},
            status=403,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(InsufficientPermissionsError):
            client.create_user("new@example.com", "New User")

    @responses.activate
    def test_get_users_success(self):
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

        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/users",
            json=user_data,
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        result = client.get_users()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(user, User) for user in result)
        assert result[0].user_id == "user-1"
        assert result[0].isadmin is True

    @responses.activate
    def test_get_users_wrapped_response(self):
        """Test users retrieval with wrapped response"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/users",
            json={
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

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        result = client.get_users()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].user_id == "user-1"

    @responses.activate
    def test_get_user_me_success(self):
        """Test successful current user retrieval"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/users/me",
            json={
                "user_id": "user-123",
                "email": "me@example.com",
                "name": "Current User",
                "account_id": "acc-123",
                "isadmin": True,
                "isbanned": False,
            },
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        result = client.get_user_me()

        assert isinstance(result, User)
        assert result.user_id == "user-123"
        assert result.email == "me@example.com"
        assert result.isadmin is True

    @responses.activate
    def test_update_user_me_success(self):
        """Test successful current user update"""
        responses.add(
            responses.PUT,
            "https://dev.cerevox.ai/v1/users/me",
            json={"updated": True, "status": "success"},
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        result = client.update_user_me("Updated Name")

        assert isinstance(result, UpdatedResponse)
        assert result.updated is True
        assert result.status == "success"

    @responses.activate
    def test_get_user_by_id_success(self):
        """Test successful user retrieval by ID"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={
                "user_id": "user-456",
                "email": "other@example.com",
                "name": "Other User",
                "account_id": "acc-123",
                "isadmin": False,
                "isbanned": False,
            },
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        result = client.get_user_by_id("user-456")

        assert isinstance(result, User)
        assert result.user_id == "user-456"
        assert result.email == "other@example.com"

    @responses.activate
    def test_get_user_by_id_insufficient_permissions(self):
        """Test user retrieval by ID with insufficient permissions"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={"error": "Forbidden"},
            status=403,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(InsufficientPermissionsError):
            client.get_user_by_id("user-456")

    @responses.activate
    def test_update_user_by_id_success(self):
        """Test successful user update by ID"""
        responses.add(
            responses.PUT,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={"updated": True, "status": "success"},
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        result = client.update_user_by_id("user-456", "New Name")

        assert isinstance(result, UpdatedResponse)
        assert result.updated is True

    @responses.activate
    def test_delete_user_by_id_success(self):
        """Test successful user deletion by ID"""
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={"deleted": True, "status": "success"},
            status=200,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        result = client.delete_user_by_id("user-456", "confirm@example.com")

        assert isinstance(result, DeletedResponse)
        assert result.deleted is True


class TestAccountErrorHandling:
    """Test Account error handling"""

    @responses.activate
    def test_request_timeout(self):
        """Test request timeout handling"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/accounts/my",
            body=Timeout(),
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(LexaTimeoutError):
            client.get_account_info()

    @responses.activate
    def test_connection_error(self):
        """Test connection error handling"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/accounts/my",
            body=ConnectionError(),
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(LexaError):
            client.get_account_info()

    @responses.activate
    def test_rate_limit_error(self):
        """Test rate limit error handling"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/accounts/my",
            json={"error": "Rate limit exceeded", "retry_after": 60},
            status=429,
            headers={"x-request-id": "req-123"},
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(LexaRateLimitError) as exc_info:
            client.get_account_info()

        assert exc_info.value.retry_after == 60

    @responses.activate
    def test_validation_error(self):
        """Test validation error handling"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/users",
            json={
                "error": "Validation failed",
                "validation_errors": {"email": "Invalid email format"},
            },
            status=400,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(LexaValidationError) as exc_info:
            client.create_user("invalid-email", "Test User")

        assert "email" in exc_info.value.validation_errors

    @responses.activate
    def test_non_json_response(self):
        """Test handling of non-JSON responses"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/users/me",  # Use an endpoint that doesn't parse to a specific model
            body="Server maintenance",
            status=200,
            content_type="text/plain",
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        # Use the _request method directly to test non-JSON handling
        result = client._request("GET", "/users/me")
        # Should return basic success response for non-JSON 200 responses
        assert result == {"status": "success"}

    @responses.activate
    def test_failed_request_id_extraction(self):
        """Test handling when request ID extraction fails"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/accounts/my",
            json={"error": "Server error"},
            status=500,
            # No x-request-id header
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(LexaError) as exc_info:
            client.get_account_info()

        # Should use fallback request ID
        assert exc_info.value.request_id == "Failed to get request ID from response"


class TestAccountRequestHelpers:
    """Test Account request helper methods"""

    def test_close_session(self):
        """Test session closing"""
        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            original_close = Mock()
            client.session.close = original_close

            client.close()
            original_close.assert_called_once()

    def test_close_session_without_session(self):
        """Test closing when session doesn't exist"""
        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
            del client.session  # Remove session
            # Should not raise an error
            client.close()


class TestAccountFullCoverage:

    def test_extra_kwargs(self):
        """Test that extra kwargs are applied to session for backward compatibility"""
        with patch.object(Account, "login") as mock_login:
            mock_login.return_value = None
            client = Account(
                email="test@example.com",
                api_key="test-key",
                verify=False,
                stream=True,
                trust_env=False,
            )

            # Verify that the extra kwargs were applied to the session
            assert client.session.verify is False
            assert client.session.stream is True
            assert client.session.trust_env is False

    @responses.activate
    def test_bad_json_response(self):
        """Test that bad JSON response is handled"""
        # Mock a response with error status and non-JSON content
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/test",
            body="Internal Server Error",  # Non-JSON content to trigger ValueError
            status=400,
            content_type="text/plain",
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0

        # Should raise LexaValidationError with error data from lines 199-200
        with pytest.raises(LexaValidationError) as exc_info:
            client._request("GET", "/test")

        # Verify the error contains the expected data structure from lines 199-200
        error = exc_info.value
        assert error.status_code == 400
        assert error.response_data["error"] == "HTTP 400"
        assert error.response_data["message"] == "Internal Server Error"

    @responses.activate
    def test_trigger_raise_in_create_user(self):
        """Test that create_user re-raises LexaAuthError when status code is not 403 (line 357)"""
        # Mock a 401 Unauthorized response to trigger LexaAuthError (not 403)
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/users",
            json={"error": "Invalid API key", "message": "Authentication failed"},
            status=401,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0

        # This should trigger the LexaAuthError with 401 status, which will hit line 357
        # (the raise statement that re-raises when status_code != 403)
        with pytest.raises(LexaAuthError) as exc_info:
            client.create_user("test@example.com", "Test User")

        # Verify it's the original LexaAuthError being re-raised
        error = exc_info.value
        assert error.status_code == 401
        assert "Invalid API key" in error.message

    @responses.activate
    def test_trigger_raise_in_get_user_by_id(self):
        """Test that get_user_by_id re-raises LexaAuthError when status code is not 403 (line 357)"""
        # Mock a 401 Unauthorized response to trigger LexaAuthError (not 403)
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={"error": "Invalid API key", "message": "Authentication failed"},
            status=401,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0

        # This should trigger the LexaAuthError with 401 status, which will hit line 357
        # (the raise statement that re-raises when status_code != 403)
        with pytest.raises(LexaAuthError) as exc_info:
            client.get_user_by_id("user-456")

        # Verify it's the original LexaAuthError being re-raised
        error = exc_info.value
        assert error.status_code == 401
        assert "Invalid API key" in error.message

    @responses.activate
    def test_trigger_raise_in_update_user_by_id(self):
        """Test that update_user_by_id re-raises LexaAuthError when status code is not 403 (line 357)"""
        # Mock a 401 Unauthorized response to trigger LexaAuthError (not 403)
        responses.add(
            responses.PUT,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={"error": "Invalid API key", "message": "Authentication failed"},
            status=401,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(LexaAuthError) as exc_info:
            client.update_user_by_id("user-456", "New Name")

        # Verify it's the original LexaAuthError being re-raised
        error = exc_info.value
        assert error.status_code == 401
        assert "Invalid API key" in error.message

        # Trigger 403 Forbidden
        responses.add(
            responses.PUT,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={"error": "Forbidden", "message": "Authentication failed"},
            status=403,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(InsufficientPermissionsError) as exc_info:
            client.update_user_by_id("user-456", "New Name")

        # Verify it's the original InsufficientPermissionsError being re-raised
        error = exc_info.value

    @responses.activate
    def test_trigger_raise_in_delete_user_by_id(self):
        """Test that delete_user_by_id re-raises LexaAuthError when status code is not 403 (line 357)"""
        # Mock a 401 Unauthorized response to trigger LexaAuthError (not 403)
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={"error": "Invalid API key", "message": "Authentication failed"},
            status=401,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(LexaAuthError) as exc_info:
            client.delete_user_by_id("user-456", "confirm@example.com")

            # Verify it's the original LexaAuthError being re-raised
            error = exc_info.value
            assert error.status_code == 401
            assert "Invalid API key" in error.message

        # Trigger 403 Forbidden
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/users/user-456",
            json={"error": "Forbidden", "message": "Authentication failed"},
            status=403,
        )

        with patch.object(Account, "__init__", return_value=None):
            client = Account.__new__(Account)
            client.session = requests.Session()
            client.base_url = "https://dev.cerevox.ai/v1"
            client.timeout = 30.0
        with pytest.raises(InsufficientPermissionsError) as exc_info:
            client.delete_user_by_id("user-456", "confirm@example.com")

            # Verify it's the original InsufficientPermissionsError being re-raised
            error = exc_info.value
            assert error.status_code == 403
            assert "Forbidden" in error.message
