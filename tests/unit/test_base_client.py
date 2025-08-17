"""
Test suite for cerevox.core.base_client

Comprehensive tests to achieve 100% code coverage for the BaseClient class,
focusing on the auth_url validation and initialization logic.
"""

import os
from unittest.mock import patch

import pytest

from cerevox.core.base_client import BaseClient
from cerevox.core.exceptions import LexaError


class TestBaseClientAuthUrl:
    """Test class for BaseClient auth_url functionality"""

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
        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(api_key=valid_api_key, base_url=valid_base_url)

            assert client.auth_url == valid_base_url
            assert client.base_url == valid_base_url

    def test_auth_url_defaults_to_base_url_when_empty_string(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url defaults to base_url when provided as empty string"""
        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=""
            )

            assert client.auth_url == valid_base_url
            assert client.base_url == valid_base_url

    def test_auth_url_defaults_to_base_url_when_none_value(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url defaults to base_url when explicitly set to None"""
        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=None
            )

            assert client.auth_url == valid_base_url
            assert client.base_url == valid_base_url

    def test_auth_url_custom_https_url(self, valid_api_key, valid_base_url):
        """Test auth_url with a valid custom HTTPS URL"""
        custom_auth_url = "https://auth.dev.cerevox.ai/v1"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
            )

            assert client.auth_url == custom_auth_url
            assert client.base_url == valid_base_url

    def test_auth_url_custom_http_url(self, valid_api_key, valid_base_url):
        """Test auth_url with a valid custom HTTP URL"""
        custom_auth_url = "http://localhost:8080/auth"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
            )

            assert client.auth_url == custom_auth_url
            assert client.base_url == valid_base_url

    def test_auth_url_strips_trailing_slash(self, valid_api_key, valid_base_url):
        """Test that auth_url strips trailing slashes"""
        custom_auth_url = "https://auth.dev.cerevox.ai/v1/"
        expected_auth_url = "https://auth.dev.cerevox.ai/v1"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
            )

            assert client.auth_url == expected_auth_url

    def test_auth_url_strips_multiple_trailing_slashes(
        self, valid_api_key, valid_base_url
    ):
        """Test that auth_url strips multiple trailing slashes"""
        custom_auth_url = "https://auth.dev.cerevox.ai/v1///"
        expected_auth_url = "https://auth.dev.cerevox.ai/v1"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
            )

            assert client.auth_url == expected_auth_url

    def test_auth_url_validation_non_string_type(self, valid_api_key, valid_base_url):
        """Test that auth_url validation fails for non-string types"""
        with pytest.raises(ValueError, match="auth_url must be a non-empty string"):
            BaseClient(api_key=valid_api_key, base_url=valid_base_url, auth_url=123)

    def test_auth_url_validation_list_type(self, valid_api_key, valid_base_url):
        """Test that auth_url validation fails for list type"""
        with pytest.raises(ValueError, match="auth_url must be a non-empty string"):
            BaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url=["https://auth.dev.cerevox.ai"],
            )

    def test_auth_url_validation_dict_type(self, valid_api_key, valid_base_url):
        """Test that auth_url validation fails for dict type"""
        with pytest.raises(ValueError, match="auth_url must be a non-empty string"):
            BaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url={"url": "https://auth.dev.cerevox.ai"},
            )

    def test_auth_url_validation_missing_protocol(self, valid_api_key, valid_base_url):
        """Test that auth_url validation fails when protocol is missing"""
        with pytest.raises(
            ValueError, match="auth_url must start with http:// or https://"
        ):
            BaseClient(
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
            BaseClient(
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
            BaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url="file:///path/to/auth",
            )

    def test_auth_url_with_port_number(self, valid_api_key, valid_base_url):
        """Test auth_url with port number"""
        custom_auth_url = "https://auth.dev.cerevox.ai:8443/v1"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
            )

            assert client.auth_url == custom_auth_url

    def test_auth_url_with_path_and_query_params(self, valid_api_key, valid_base_url):
        """Test auth_url with path and query parameters"""
        custom_auth_url = "https://auth.dev.cerevox.ai/oauth/v1?version=2"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
            )

            assert client.auth_url == custom_auth_url

    def test_auth_url_localhost_with_port(self, valid_api_key, valid_base_url):
        """Test auth_url with localhost and port"""
        custom_auth_url = "http://localhost:3000/auth"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
            )

            assert client.auth_url == custom_auth_url

    def test_auth_url_ip_address(self, valid_api_key, valid_base_url):
        """Test auth_url with IP address"""
        custom_auth_url = "http://192.168.1.100:8080/auth"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, auth_url=custom_auth_url
            )

            assert client.auth_url == custom_auth_url

    def test_auth_url_different_from_base_url_independence(self, valid_api_key):
        """Test that auth_url and base_url can be completely different and independent"""
        base_url = "https://dev.cerevox.ai/v1"
        auth_url = "https://completely-different-auth.example.com/oauth"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=base_url, auth_url=auth_url
            )

            assert client.base_url == base_url
            assert client.auth_url == auth_url
            assert client.auth_url != client.base_url

    @patch.dict(os.environ, {"CEREVOX_API_KEY": "env-api-key"})
    def test_auth_url_with_environment_api_key(self, valid_base_url):
        """Test auth_url functionality when API key comes from environment"""
        custom_auth_url = "https://auth.dev.cerevox.ai/v1"

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(base_url=valid_base_url, auth_url=custom_auth_url)

            assert client.auth_url == custom_auth_url
            assert client.api_key == "env-api-key"

    def test_auth_url_case_sensitivity_https(self, valid_api_key, valid_base_url):
        """Test that auth_url validation is case-sensitive for HTTPS"""
        # This should fail because HTTPS (uppercase) is not valid
        with pytest.raises(
            ValueError, match="auth_url must start with http:// or https://"
        ):
            BaseClient(
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
            BaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                auth_url="HTTP://auth.dev.cerevox.ai/v1",
            )

    def test_session_initialization(self, valid_api_key, valid_base_url):
        """Test that session is properly initialized"""
        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(api_key=valid_api_key, base_url=valid_base_url)

            assert client.session is not None
            assert hasattr(client, "session")

    def test_timeout_configuration(self, valid_api_key, valid_base_url):
        """Test that timeout is properly configured"""
        custom_timeout = 60.0

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key, base_url=valid_base_url, timeout=custom_timeout
            )

            assert client.timeout == custom_timeout

    def test_max_retries_configuration(self, valid_api_key, valid_base_url):
        """Test that max_retries is properly configured"""
        custom_retries = 5

        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key=valid_api_key,
                base_url=valid_base_url,
                max_retries=custom_retries,
            )

            assert client.max_retries == custom_retries


class TestBaseClientInitialization:
    """Test class for BaseClient initialization functionality"""

    @pytest.fixture
    def valid_base_url(self):
        """Fixture providing a valid base URL"""
        return "https://dev.cerevox.ai/v1"

    def test_ensure_valid_token_no_access_token_raises_error(self, valid_base_url):
        """Test _ensure_valid_token raises LexaError when no access token is available"""
        # Create client with API key initially to pass __init__ validation
        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key="temp-key",
                base_url=valid_base_url,
                auth_url="https://auth.dev.cerevox.ai/v1",
            )

        # Clear the access token to simulate the scenario where no token is available
        client.access_token = None
        client.token_expires_at = None

        # Test that _ensure_valid_token raises LexaError with expected message
        with pytest.raises(LexaError, match="No access token available") as exc_info:
            client._ensure_valid_token()

        # Verify the error details
        error = exc_info.value
        assert error.message == "No access token available"
        assert error.request_id == "Failed to get request ID from response"

    def test_ensure_valid_token_no_token_expires_at_raises_error(self, valid_base_url):
        """Test _ensure_valid_token raises LexaError when access_token exists but token_expires_at is None"""
        # Create client with API key initially to pass __init__ validation
        with patch.object(BaseClient, "_login") as mock_login:
            mock_login.return_value = None
            client = BaseClient(
                api_key="temp-key",
                base_url=valid_base_url,
                auth_url="https://auth.dev.cerevox.ai/v1",
            )

        # Set access token but clear token_expires_at to simulate the scenario
        client.access_token = "some-access-token"
        client.token_expires_at = None

        # Test that _ensure_valid_token raises LexaError with expected message
        with pytest.raises(LexaError, match="No access token available") as exc_info:
            client._ensure_valid_token()

        # Verify the error details
        error = exc_info.value
        assert error.message == "No access token available"
        assert error.request_id == "Failed to get request ID from response"
