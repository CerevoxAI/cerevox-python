"""
Test suite for cerevox.core.async_base_client

Comprehensive tests to achieve 100% code coverage for the AsyncBaseClient class,
focusing on the auth_url validation and initialization logic.
"""

import os
import time
from unittest.mock import AsyncMock, patch

import pytest

from cerevox.core.async_base_client import AsyncBaseClient
from cerevox.core.exceptions import LexaError
from cerevox.core.models import TokenResponse


class TestAsyncBaseClientAuthUrl:
    """Test class for AsyncBaseClient auth_url functionality"""

    @pytest.fixture
    def valid_api_key(self):
        """Fixture providing a valid API key"""
        return "test-api-key-12345"

    @pytest.fixture
    def valid_base_url(self):
        """Fixture providing a valid base URL"""
        return "https://dev.cerevox.ai/v1"

    def test_auth_url_defaults_to_base_url_when_none(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url defaults to base_url when not provided"""
        client = AsyncBaseClient(api_key=valid_api_key, base_url=valid_base_url)

        assert client.auth_url == valid_base_url
        assert client.base_url == valid_base_url

    def test_auth_url_defaults_to_base_url_when_empty_string(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url defaults to base_url when provided as empty string"""
        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=""
        )

        assert client.auth_url == valid_base_url
        assert client.base_url == valid_base_url

    def test_auth_url_defaults_to_base_url_when_none_value(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url defaults to base_url when explicitly set to None"""
        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=None
        )

        assert client.auth_url == valid_base_url
        assert client.base_url == valid_base_url

    def test_auth_url_custom_https_url(self, valid_api_key, valid_base_url):
        """Test auth_url with a valid custom HTTPS URL"""
        custom_auth_url = "https://auth.dev.cerevox.ai/v1"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
        )

        assert client.auth_url == custom_auth_url
        assert client.base_url == valid_base_url

    def test_auth_url_custom_http_url(self, valid_api_key, valid_base_url):
        """Test auth_url with a valid custom HTTP URL"""
        custom_auth_url = "http://localhost:8080/auth"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
        )

        assert client.auth_url == custom_auth_url
        assert client.base_url == valid_base_url

    def test_auth_url_strips_trailing_slash(self, valid_api_key, valid_base_url):
        """Test that auth_url strips trailing slashes"""
        custom_auth_url = "https://auth.dev.cerevox.ai/v1/"
        expected_auth_url = "https://auth.dev.cerevox.ai/v1"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
        )

        assert client.auth_url == expected_auth_url

    def test_auth_url_strips_multiple_trailing_slashes(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url strips multiple trailing slashes"""
        custom_auth_url = "https://auth.dev.cerevox.ai/v1///"
        expected_auth_url = "https://auth.dev.cerevox.ai/v1"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
        )

        assert client.auth_url == expected_auth_url

    def test_auth_url_validation_non_string_type(self, valid_api_key, valid_base_url):
        """Test that auth_url validation fails for non-string types"""
        with pytest.raises(ValueError, match="auth_url must be a non-empty string"):
            AsyncBaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=123
            )

    def test_auth_url_validation_list_type(self, valid_api_key, valid_base_url):
        """Test that auth_url validation fails for list type"""
        with pytest.raises(ValueError, match="auth_url must be a non-empty string"):
            AsyncBaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url=["https://auth.dev.cerevox.ai"],
            )

    def test_auth_url_validation_dict_type(self, valid_api_key, valid_base_url):
        """Test that auth_url validation fails for dict type"""
        with pytest.raises(ValueError, match="auth_url must be a non-empty string"):
            AsyncBaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url={"url": "https://auth.dev.cerevox.ai"},
            )

    def test_auth_url_validation_missing_protocol(self, valid_api_key, valid_base_url):
        """Test that auth_url validation fails when protocol is missing"""
        with pytest.raises(
            ValueError, match="auth_url must start with http:// or https://"
        ):
            AsyncBaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url="auth.dev.cerevox.ai/v1",
            )

    def test_auth_url_validation_invalid_protocol_ftp(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url validation fails for invalid protocol (ftp)"""
        with pytest.raises(
            ValueError, match="auth_url must start with http:// or https://"
        ):
            AsyncBaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url="ftp://auth.dev.cerevox.ai/v1",
            )

    def test_auth_url_validation_invalid_protocol_file(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url validation fails for invalid protocol (file)"""
        with pytest.raises(
            ValueError, match="auth_url must start with http:// or https://"
        ):
            AsyncBaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url="file:///path/to/auth",
            )

    def test_auth_url_with_port_number(self, valid_api_key, valid_base_url):
        """Test auth_url with port number"""
        custom_auth_url = "https://auth.dev.cerevox.ai:8443/v1"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
        )

        assert client.auth_url == custom_auth_url

    def test_auth_url_with_path_and_query_params(self, valid_api_key, valid_base_url):
        """Test auth_url with path and query parameters"""
        custom_auth_url = "https://auth.dev.cerevox.ai/oauth/v1?version=2"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
        )

        assert client.auth_url == custom_auth_url

    def test_auth_url_localhost_with_port(self, valid_api_key, valid_base_url):
        """Test auth_url with localhost and port"""
        custom_auth_url = "http://localhost:3000/auth"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
        )

        assert client.auth_url == custom_auth_url

    def test_auth_url_ip_address(self, valid_api_key, valid_base_url):
        """Test auth_url with IP address"""
        custom_auth_url = "http://192.168.1.100:8080/auth"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
        )

        assert client.auth_url == custom_auth_url

    def test_auth_url_different_from_base_url_independence(self, valid_api_key):
        """Test that auth_url and base_url can be completely different and independent"""
        base_url = "https://dev.cerevox.ai/v1"
        auth_url = "https://completely-different-auth.example.com/oauth"

        client = AsyncBaseClient(
            api_key=valid_api_key, base_url=base_url, auth_url=auth_url
        )

        assert client.base_url == base_url
        assert client.auth_url == auth_url
        assert client.auth_url != client.base_url

    @patch.dict(os.environ, {"CEREVOX_API_KEY": "env-api-key"})
    def test_auth_url_with_environment_api_key(self, valid_base_url):
        """Test auth_url functionality when API key comes from environment"""
        custom_auth_url = "https://auth.dev.cerevox.ai/v1"

        client = AsyncBaseClient(base_url=valid_base_url, auth_url=custom_auth_url)

        assert client.auth_url == custom_auth_url
        assert client.api_key == "env-api-key"

    def test_auth_url_case_sensitivity_https(self, valid_api_key, valid_base_url):
        """Test that auth_url validation is case-sensitive for HTTPS"""
        # This should fail because HTTPS (uppercase) is not valid
        with pytest.raises(
            ValueError, match="auth_url must start with http:// or https://"
        ):
            AsyncBaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url="HTTPS://auth.dev.cerevox.ai/v1",
            )

    def test_auth_url_case_sensitivity_http(self, valid_api_key, valid_base_url):
        """Test that auth_url validation is case-sensitive for HTTP"""
        # This should fail because HTTP (uppercase) is not valid
        with pytest.raises(
            ValueError, match="auth_url must start with http:// or https://"
        ):
            AsyncBaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url="HTTP://auth.dev.cerevox.ai/v1",
            )


class TestAsyncBaseClientInitialization:
    """Test class for AsyncBaseClient initialization functionality"""

    @pytest.fixture
    def valid_base_url(self):
        """Fixture providing a valid base URL"""
        return "https://dev.cerevox.ai/v1"

    @patch.dict(os.environ, {}, clear=True)
    async def test_start_session_without_api_key_raises_error(self, valid_base_url):
        """Test start_session without API key raises ValueError"""
        # Create client with API key initially to pass __init__ validation
        client = AsyncBaseClient(
            api_key="temp-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Clear the API key to test the start_session validation
        client.api_key = None

        # Mock the _login method to avoid actual authentication
        with patch.object(client, "_login") as mock_login:
            with pytest.raises(
                ValueError, match="API key is required for authentication"
            ):
                await client.start_session()

            # Clean up any session that might have been created
            await client.close_session()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_no_access_token_raises_error(
        self, valid_base_url
    ):
        """Test _ensure_valid_token raises LexaError when no access token is available"""
        # Create client with API key initially to pass __init__ validation
        client = AsyncBaseClient(
            api_key="temp-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Clear the access token to simulate the scenario where no token is available
        client.access_token = None
        client.token_expires_at = None

        # Test that _ensure_valid_token raises LexaError with expected message
        with pytest.raises(LexaError, match="No access token available") as exc_info:
            await client._ensure_valid_token()

        # Verify the error details
        error = exc_info.value
        assert error.message == "No access token available"
        assert error.request_id == "Failed to get request ID from response"

        # Clean up any session that might have been created
        await client.close_session()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_no_token_expires_at_raises_error(
        self, valid_base_url
    ):
        """Test _ensure_valid_token raises LexaError when access_token exists but token_expires_at is None"""
        # Create client with API key initially to pass __init__ validation
        client = AsyncBaseClient(
            api_key="temp-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Set access token but clear token_expires_at to simulate the scenario
        client.access_token = "some-access-token"
        client.token_expires_at = None

        # Test that _ensure_valid_token raises LexaError with expected message
        with pytest.raises(LexaError, match="No access token available") as exc_info:
            await client._ensure_valid_token()

        # Verify the error details
        error = exc_info.value
        assert error.message == "No access token available"
        assert error.request_id == "Failed to get request ID from response"

        # Clean up any session that might have been created
        await client.close_session()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_expired_with_refresh_token_success(
        self, valid_base_url
    ):
        """Test _ensure_valid_token refreshes token when expired and refresh token is available"""

        # Create client with API key
        client = AsyncBaseClient(
            api_key="test-api-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Set up expired token scenario
        current_time = time.time()
        client.access_token = "expired-token"
        client.refresh_token = "valid-refresh-token"
        client.token_expires_at = current_time - 10  # Token expired 10 seconds ago

        # Mock the _refresh_token method to simulate successful refresh
        mock_token_response = TokenResponse(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            expires_in=3600,
            token_type="Bearer",
        )

        with patch.object(
            client, "_refresh_token", new_callable=AsyncMock
        ) as mock_refresh:
            mock_refresh.return_value = mock_token_response

            # This should not raise an error and should refresh the token
            await client._ensure_valid_token()

            # Verify _refresh_token was called with the correct refresh token
            mock_refresh.assert_called_once_with("valid-refresh-token")

        # Clean up
        await client.close_session()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_expiring_soon_with_refresh_token_success(
        self, valid_base_url
    ):
        """Test _ensure_valid_token refreshes token when expiring within 60 seconds"""

        # Create client with API key
        client = AsyncBaseClient(
            api_key="test-api-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Set up token expiring soon scenario (expires in 30 seconds)
        current_time = time.time()
        client.access_token = "expiring-token"
        client.refresh_token = "valid-refresh-token"
        client.token_expires_at = current_time + 30  # Token expires in 30 seconds

        # Mock the _refresh_token method to simulate successful refresh
        mock_token_response = TokenResponse(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            expires_in=3600,
            token_type="Bearer",
        )

        with patch.object(
            client, "_refresh_token", new_callable=AsyncMock
        ) as mock_refresh:
            mock_refresh.return_value = mock_token_response

            # This should not raise an error and should refresh the token
            await client._ensure_valid_token()

            # Verify _refresh_token was called with the correct refresh token
            mock_refresh.assert_called_once_with("valid-refresh-token")

        # Clean up
        await client.close_session()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_expired_no_refresh_token_raises_error(
        self, valid_base_url
    ):
        """Test _ensure_valid_token raises LexaError when token is expired and no refresh token available"""

        # Create client with API key
        client = AsyncBaseClient(
            api_key="test-api-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Set up expired token scenario without refresh token
        current_time = time.time()
        client.access_token = "expired-token"
        client.refresh_token = None  # No refresh token available
        client.token_expires_at = current_time - 10  # Token expired 10 seconds ago

        # Test that _ensure_valid_token raises LexaError with expected message
        with pytest.raises(LexaError, match="No refresh token available") as exc_info:
            await client._ensure_valid_token()

        # Verify the error details
        error = exc_info.value
        assert error.message == "No refresh token available"
        assert error.request_id == "Failed to get request ID from response"

        # Clean up
        await client.close_session()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_expiring_soon_no_refresh_token_raises_error(
        self, valid_base_url
    ):
        """Test _ensure_valid_token raises LexaError when token is expiring soon and no refresh token available"""

        # Create client with API key
        client = AsyncBaseClient(
            api_key="test-api-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Set up token expiring soon scenario without refresh token
        current_time = time.time()
        client.access_token = "expiring-token"
        client.refresh_token = None  # No refresh token available
        client.token_expires_at = (
            current_time + 30
        )  # Token expires in 30 seconds (within 60 second threshold)

        # Test that _ensure_valid_token raises LexaError with expected message
        with pytest.raises(LexaError, match="No refresh token available") as exc_info:
            await client._ensure_valid_token()

        # Verify the error details
        error = exc_info.value
        assert error.message == "No refresh token available"
        assert error.request_id == "Failed to get request ID from response"

        # Clean up
        await client.close_session()

    @pytest.mark.asyncio
    async def test_ensure_valid_token_valid_token_no_refresh_needed(
        self, valid_base_url
    ):
        """Test _ensure_valid_token does not refresh when token is still valid"""

        # Create client with API key
        client = AsyncBaseClient(
            api_key="test-api-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Set up valid token scenario (expires in 2 hours)
        current_time = time.time()
        client.access_token = "valid-token"
        client.refresh_token = "refresh-token"
        client.token_expires_at = current_time + 7200  # Token expires in 2 hours

        # Mock the _refresh_token method to ensure it's not called
        with patch.object(
            client, "_refresh_token", new_callable=AsyncMock
        ) as mock_refresh:
            # This should not raise an error and should not refresh the token
            await client._ensure_valid_token()

            # Verify _refresh_token was NOT called
            mock_refresh.assert_not_called()

        # Clean up
        await client.close_session()

    @pytest.mark.asyncio
    async def test_refresh_token_no_api_key_raises_error(self, valid_base_url):
        """Test _refresh_token raises LexaError when API key is None"""

        # Create client with API key initially to pass __init__ validation
        client = AsyncBaseClient(
            api_key="temp-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Clear the API key to simulate the scenario where it's missing during refresh
        client.api_key = None

        # Test that _refresh_token raises LexaError with expected message
        with pytest.raises(
            LexaError, match="API key is required for token refresh"
        ) as exc_info:
            await client._refresh_token("some-refresh-token")

        # Verify the error details
        error = exc_info.value
        assert error.message == "API key is required for token refresh"
        assert error.request_id == "Failed to get request ID from response"

        # Clean up
        await client.close_session()

    @pytest.mark.asyncio
    async def test_refresh_token_empty_api_key_raises_error(self, valid_base_url):
        """Test _refresh_token raises LexaError when API key is empty string"""

        # Create client with API key initially to pass __init__ validation
        client = AsyncBaseClient(
            api_key="temp-key",
            base_url=valid_base_url,
            auth_url="https://auth.dev.cerevox.ai/v1",
        )

        # Set API key to empty string to simulate the scenario
        client.api_key = ""

        # Test that _refresh_token raises LexaError with expected message
        with pytest.raises(
            LexaError, match="API key is required for token refresh"
        ) as exc_info:
            await client._refresh_token("some-refresh-token")

        # Verify the error details
        error = exc_info.value
        assert error.message == "API key is required for token refresh"
        assert error.request_id == "Failed to get request ID from response"

        # Clean up
        await client.close_session()
