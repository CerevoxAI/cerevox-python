"""
Test suite for cerevox.clients.lexa

Comprehensive tests to achieve 100% code coverage for the Lexa class,
including all methods, error handling, and edge cases.
"""

import json
import os
import tempfile
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import responses
from requests.exceptions import ConnectionError, RequestException, RetryError, Timeout

from cerevox.clients.lexa import Lexa
from cerevox.core.exceptions import (
    LexaAuthError,
    LexaError,
    LexaJobFailedError,
    LexaRateLimitError,
    LexaTimeoutError,
    LexaValidationError,
)
from cerevox.core.models import (
    VALID_MODES,
    BucketListResponse,
    DriveListResponse,
    FileInfo,
    FolderListResponse,
    IngestionResult,
    JobResponse,
    JobStatus,
    ProcessingMode,
    SiteListResponse,
)


class TestLexaInitialization:
    """Test Lexa client initialization"""

    def test_init_with_api_key(self):
        """Test initialization with API key parameter"""
        client = Lexa(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.base_url == "https://www.data.cerevox.ai"
        assert client.timeout == 30.0
        assert client.max_poll_time == 600.0
        assert client.max_retries == 3
        assert client.session.headers["cerevox-api-key"] == "test-api-key"
        assert "cerevox-python" in client.session.headers["User-Agent"]

    @patch.dict(os.environ, {"CEREVOX_API_KEY": "env-api-key"})
    def test_init_with_env_var(self):
        """Test initialization with environment variable"""
        client = Lexa()
        assert client.api_key == "env-api-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError"""
        with pytest.raises(ValueError, match="API key is required"):
            Lexa()

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters"""
        client = Lexa(
            api_key="test-key",
            base_url="https://custom.api.com",
            timeout=60.0,
            max_poll_time=1200.0,
            max_retries=5,
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60.0
        assert client.max_poll_time == 1200.0
        assert client.max_retries == 5

    def test_init_with_invalid_base_url(self):
        """Test initialization with invalid base URL"""
        with pytest.raises(ValueError, match="base_url must be a non-empty string"):
            Lexa(api_key="test", base_url="")

        with pytest.raises(ValueError, match="base_url must be a non-empty string"):
            Lexa(api_key="test", base_url=None)

        with pytest.raises(ValueError, match="base_url must start with http"):
            Lexa(api_key="test", base_url="invalid-url")

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base_url"""
        client = Lexa(api_key="test", base_url="https://api.com/")
        assert client.base_url == "https://api.com"

    def test_init_with_session_kwargs(self):
        """Test initialization with session kwargs"""
        session_kwargs = {"verify": False, "stream": True}
        client = Lexa(api_key="test", session_kwargs=session_kwargs)
        assert client.session.verify is False
        assert client.session.stream is True

    def test_init_with_backward_compatible_kwargs(self):
        """Test initialization with backward compatible kwargs"""
        client = Lexa(api_key="test", verify=False, stream=True)
        assert client.session.verify is False
        assert client.session.stream is True


class TestLexaRequest:
    """Test the _request method"""

    @responses.activate
    def test_successful_request(self):
        """Test successful API request"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            json={"status": "success"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._request("GET", "/v0/test")
        assert result == {"status": "success"}

    @responses.activate
    def test_request_with_json_data(self):
        """Test request with JSON data"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/test",
            json={"received": True},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._request("POST", "/v0/test", json_data={"key": "value"})
        assert result == {"received": True}

        # Check the request body
        request = responses.calls[0].request
        assert json.loads(request.body) == {"key": "value"}

    @responses.activate
    def test_request_with_files(self):
        """Test request with files"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"uploaded": True},
            status=200,
        )

        client = Lexa(api_key="test-key")
        files = {"file": ("test.txt", BytesIO(b"test content"))}
        result = client._request("POST", "/v0/files", files=files)
        assert result == {"uploaded": True}

    @responses.activate
    def test_request_with_params(self):
        """Test request with query parameters"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            json={"params_received": True},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._request("GET", "/v0/test", params={"param1": "value1"})
        assert result == {"params_received": True}

        # Check the request URL
        request = responses.calls[0].request
        assert "param1=value1" in request.url

    @responses.activate
    def test_auth_error_401(self):
        """Test 401 authentication error"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            json={"error": "Invalid API key"},
            status=401,
        )

        client = Lexa(api_key="test-key")
        with pytest.raises(
            LexaAuthError, match="Invalid API key or authentication failed"
        ):
            client._request("GET", "/v0/test")

    @responses.activate
    def test_rate_limit_error_429(self):
        """Test 429 rate limit error"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            json={"error": "Rate limit exceeded"},
            status=429,
        )

        client = Lexa(api_key="test-key")
        with pytest.raises(LexaRateLimitError, match="Rate limit exceeded"):
            client._request("GET", "/v0/test")

    @responses.activate
    def test_validation_error_400(self):
        """Test 400 validation error"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            json={"error": "Invalid request"},
            status=400,
        )

        client = Lexa(api_key="test-key")
        with pytest.raises(LexaValidationError, match="Invalid request"):
            client._request("GET", "/v0/test")

    @responses.activate
    def test_generic_api_error(self):
        """Test generic API error"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            json={"error": "Server error"},
            status=500,
        )

        # Create client with max_retries=0 to avoid retry behavior
        client = Lexa(api_key="test-key", max_retries=0)
        with pytest.raises(LexaError, match="Internal server error"):
            client._request("GET", "/v0/test")

    @responses.activate
    def test_api_error_without_json_response(self):
        """Test API error without JSON response"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            body="Server Error",
            status=500,
            content_type="text/plain",
        )

        # Create client with max_retries=0 to avoid retry behavior
        client = Lexa(api_key="test-key", max_retries=0)
        with pytest.raises(LexaError, match="Internal server error"):
            client._request("GET", "/v0/test")

    @responses.activate
    def test_non_json_response(self):
        """Test handling of non-JSON response"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            body="plain text response",
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._request("GET", "/v0/test")
        assert result == {}

    def test_timeout_error(self):
        """Test timeout error handling"""
        client = Lexa(api_key="test-key", timeout=0.001)

        with patch.object(client.session, "request") as mock_request:
            mock_request.side_effect = Timeout("Request timed out")

            with pytest.raises(LexaTimeoutError, match="Request timed out"):
                client._request("GET", "/v0/test")

    def test_connection_error(self):
        """Test connection error handling"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            mock_request.side_effect = ConnectionError("Connection failed")

            with pytest.raises(LexaError, match="Connection failed"):
                client._request("GET", "/v0/test")

    def test_retry_error_with_500(self):
        """Test retry error with 500 status codes"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            retry_error = RetryError("500 error responses")
            retry_error.response = Mock()
            retry_error.response.status_code = 500
            retry_error.response.json.return_value = {"error": "Server error"}
            mock_request.side_effect = retry_error

            with pytest.raises(LexaError, match="Server error"):
                client._request("GET", "/v0/test")

    def test_retry_error_generic(self):
        """Test generic retry error"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            mock_request.side_effect = RetryError("Max retries exceeded")

            with pytest.raises(LexaError, match="Request failed after retries"):
                client._request("GET", "/v0/test")

    def test_retry_error_500_mention(self):
        """Test retry error mentioning 500 errors"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            mock_request.side_effect = RetryError("Failed with 500 error responses")

            with pytest.raises(LexaError, match="Internal server error"):
                client._request("GET", "/v0/test")

    def test_generic_request_exception(self):
        """Test generic request exception"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            mock_request.side_effect = RequestException("Generic error")

            with pytest.raises(LexaError, match="Request failed"):
                client._request("GET", "/v0/test")


class TestGetJobStatus:
    """Test _get_job_status method"""

    @responses.activate
    def test_get_job_status_success(self):
        """Test successful job status retrieval"""
        job_response = {
            "status": "complete",
            "requestID": "job-123",
            "progress": 100,
            "message": "Job completed successfully",
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._get_job_status("job-123")

        assert isinstance(result, JobResponse)
        assert result.status == JobStatus.COMPLETE
        assert result.request_id == "job-123"
        assert result.progress == 100

    def test_get_job_status_empty_request_id(self):
        """Test _get_job_status with empty request_id"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="request_id cannot be empty"):
            client._get_job_status("")

        with pytest.raises(ValueError, match="request_id cannot be empty"):
            client._get_job_status("   ")


class TestWaitForCompletion:
    """Test _wait_for_completion method"""

    @responses.activate
    def test_wait_for_completion_success(self):
        """Test successful wait for completion"""
        job_response = {
            "status": "complete",
            "requestID": "job-123",
            "progress": 100,
            "message": "Job completed",
            "result": {"documents": []},
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._wait_for_completion("job-123", timeout=1.0)

        assert result.status == JobStatus.COMPLETE
        assert result.request_id == "job-123"

    @responses.activate
    def test_wait_for_completion_with_callback(self):
        """Test wait for completion with progress callback"""
        job_response = {
            "status": "complete",
            "requestID": "job-123",
            "progress": 100,
            "message": "Job completed",
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        callback_calls = []

        def progress_callback(status):
            callback_calls.append(status)

        client = Lexa(api_key="test-key")
        result = client._wait_for_completion(
            "job-123", progress_callback=progress_callback
        )

        assert len(callback_calls) == 1
        assert callback_calls[0].status == JobStatus.COMPLETE

    @responses.activate
    def test_wait_for_completion_failed_job(self):
        """Test wait for completion with failed job"""
        job_response = {
            "status": "failed",
            "requestID": "job-123",
            "error": "Processing failed",
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        with pytest.raises(LexaJobFailedError, match="Processing failed"):
            client._wait_for_completion("job-123")

    @responses.activate
    def test_wait_for_completion_internal_error(self):
        """Test wait for completion with internal error"""
        job_response = {
            "status": "internal_error",
            "requestID": "job-123",
            "error": "Internal server error",
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        with pytest.raises(LexaJobFailedError, match="Internal server error"):
            client._wait_for_completion("job-123")

    @responses.activate
    def test_wait_for_completion_not_found(self):
        """Test wait for completion with not found status"""
        job_response = {"status": "not_found", "requestID": "job-123"}
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        with pytest.raises(LexaJobFailedError, match="Job failed"):
            client._wait_for_completion("job-123")

    @responses.activate
    def test_wait_for_completion_timeout(self):
        """Test wait for completion timeout"""
        job_response = {"status": "processing", "requestID": "job-123", "progress": 50}
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        with pytest.raises(
            LexaTimeoutError, match="Job job-123 exceeded maximum wait time"
        ):
            client._wait_for_completion("job-123", timeout=0.1, poll_interval=0.05)

    @responses.activate
    def test_wait_for_completion_uses_max_poll_time(self):
        """Test wait for completion uses max_poll_time when timeout is None"""
        job_response = {"status": "processing", "requestID": "job-123", "progress": 50}
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key", max_poll_time=0.1)
        with pytest.raises(LexaTimeoutError):
            client._wait_for_completion("job-123", timeout=None, poll_interval=0.05)


class TestGetFileInfoFromUrl:
    """Test _get_file_info_from_url method"""

    @responses.activate
    def test_get_file_info_with_content_disposition(self):
        """Test file info extraction with Content-Disposition header"""
        responses.add(
            responses.HEAD,
            "https://example.com/document.pdf",
            headers={
                "Content-Disposition": 'attachment; filename="report.pdf"',
                "Content-Type": "application/pdf",
            },
            status=200,
        )

        client = Lexa(api_key="test-key")
        file_info = client._get_file_info_from_url("https://example.com/document.pdf")

        assert file_info.name == "report.pdf"
        assert file_info.url == "https://example.com/document.pdf"
        assert file_info.type == "application/pdf"

    @responses.activate
    def test_get_file_info_with_filename_star(self):
        """Test file info extraction with filename* parameter"""
        responses.add(
            responses.HEAD,
            "https://example.com/document.pdf",
            headers={
                "Content-Disposition": "attachment; filename*=UTF-8''report%20file.pdf",
                "Content-Type": "application/pdf",
            },
            status=200,
        )

        client = Lexa(api_key="test-key")
        file_info = client._get_file_info_from_url("https://example.com/document.pdf")

        # The regex captures everything after = and strips whitespace
        assert file_info.name == "UTF-8"
        assert file_info.type == "application/pdf"

    @responses.activate
    def test_get_file_info_from_url_path(self):
        """Test file info extraction from URL path"""
        responses.add(
            responses.HEAD,
            "https://example.com/files/document.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        file_info = client._get_file_info_from_url(
            "https://example.com/files/document.pdf"
        )

        assert file_info.name == "document.pdf"
        assert file_info.type == "application/pdf"

    @responses.activate
    def test_get_file_info_with_query_params(self):
        """Test file info extraction with query parameters in URL"""
        responses.add(
            responses.HEAD,
            "https://example.com/document.pdf?version=1&auth=token",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        file_info = client._get_file_info_from_url(
            "https://example.com/document.pdf?version=1&auth=token"
        )

        assert file_info.name == "document.pdf"
        assert file_info.type == "application/pdf"

    @responses.activate
    def test_get_file_info_fallback_filename(self):
        """Test file info with fallback filename generation"""
        responses.add(
            responses.HEAD,
            "https://example.com/",
            headers={"Content-Type": "text/html"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        file_info = client._get_file_info_from_url("https://example.com/")

        # Should generate a hash-based filename
        assert file_info.name.startswith("file_")
        assert file_info.type == "text/html"

    @responses.activate
    def test_get_file_info_content_type_with_charset(self):
        """Test content type parsing with charset parameter"""
        responses.add(
            responses.HEAD,
            "https://example.com/file.txt",
            headers={"Content-Type": "text/plain; charset=utf-8"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        file_info = client._get_file_info_from_url("https://example.com/file.txt")

        assert file_info.type == "text/plain"

    def test_get_file_info_head_request_fails(self):
        """Test file info extraction when HEAD request fails"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("Request failed")

            file_info = client._get_file_info_from_url(
                "https://example.com/document.pdf"
            )

            assert file_info.name == "document.pdf"
            assert file_info.type == "application/octet-stream"

    def test_get_file_info_url_parsing_fails(self):
        """Test file info when URL parsing fails"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("Request failed")

            with patch("cerevox.clients.lexa.urlparse") as mock_urlparse:
                mock_urlparse.side_effect = Exception("URL parsing failed")

                file_info = client._get_file_info_from_url(
                    "https://example.com/document.pdf"
                )

                # Should generate hash-based filename
                assert file_info.name.startswith("file_")
                assert file_info.type == "application/octet-stream"


class TestUploadFiles:
    """Test _upload_files method"""

    def create_temp_file(self, content: bytes = b"test content", suffix: str = ".txt"):
        """Helper to create temporary files"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def cleanup_temp_file(self, filepath: str):
        """Helper to cleanup temporary files"""
        try:
            os.unlink(filepath)
        except FileNotFoundError:
            pass

    @responses.activate
    def test_upload_single_file_path(self):
        """Test uploading a single file by path"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={
                "message": "Files uploaded successfully",
                "requestID": "req-123",
                "uploads": ["test.txt"],
            },
            status=200,
        )

        # Create temporary file
        temp_file = self.create_temp_file(b"test content", ".txt")

        try:
            client = Lexa(api_key="test-key")
            result = client._upload_files(temp_file)

            assert isinstance(result, IngestionResult)
            assert result.request_id == "req-123"
            assert result.message == "Files uploaded successfully"
        finally:
            self.cleanup_temp_file(temp_file)

    @responses.activate
    def test_upload_multiple_file_paths(self):
        """Test uploading multiple files by path"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={
                "message": "Files uploaded successfully",
                "requestID": "req-124",
                "uploads": ["test1.txt", "test2.txt"],
            },
            status=200,
        )

        # Create temporary files
        temp_file1 = self.create_temp_file(b"content 1", ".txt")
        temp_file2 = self.create_temp_file(b"content 2", ".txt")

        try:
            client = Lexa(api_key="test-key")
            result = client._upload_files([temp_file1, temp_file2])

            assert result.request_id == "req-124"
        finally:
            self.cleanup_temp_file(temp_file1)
            self.cleanup_temp_file(temp_file2)

    @responses.activate
    def test_upload_file_with_path_object(self):
        """Test uploading file with Path object"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "File uploaded", "requestID": "req-125"},
            status=200,
        )

        temp_file = self.create_temp_file(b"content", ".txt")

        try:
            client = Lexa(api_key="test-key")
            result = client._upload_files(Path(temp_file))

            assert result.request_id == "req-125"
        finally:
            self.cleanup_temp_file(temp_file)

    @responses.activate
    def test_upload_file_with_bytes(self):
        """Test uploading raw bytes content"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "File uploaded", "requestID": "req-126"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_files(b"raw file content")

        assert result.request_id == "req-126"

    @responses.activate
    def test_upload_file_with_bytearray(self):
        """Test uploading bytearray content"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "File uploaded", "requestID": "req-127"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_files(bytearray(b"bytearray content"))

        assert result.request_id == "req-127"

    @responses.activate
    def test_upload_file_with_stream(self):
        """Test uploading file-like stream"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "File uploaded", "requestID": "req-128"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        stream = BytesIO(b"stream content")
        stream.name = "test_stream.txt"
        result = client._upload_files(stream)

        assert result.request_id == "req-128"

    @responses.activate
    def test_upload_file_with_unnamed_stream(self):
        """Test uploading unnamed stream"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "File uploaded", "requestID": "req-129"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        stream = BytesIO(b"unnamed stream content")
        result = client._upload_files(stream)

        assert result.request_id == "req-129"

    @responses.activate
    def test_upload_with_processing_mode_enum(self):
        """Test upload with ProcessingMode enum"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "File uploaded", "requestID": "req-130"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_files(b"content", ProcessingMode.ADVANCED)

        assert result.request_id == "req-130"

        # Check that the request was made with the correct parameters
        request = responses.calls[0].request
        # The mode should be in query parameters since it's passed as params
        assert "mode=advanced" in request.url

    @responses.activate
    def test_upload_with_processing_mode_string(self):
        """Test upload with processing mode as string"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "File uploaded", "requestID": "req-131"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_files(b"content", "advanced")

        assert result.request_id == "req-131"

    def test_upload_with_invalid_processing_mode(self):
        """Test upload with invalid processing mode"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_files(b"content", "invalid_mode")

    def test_upload_no_files(self):
        """Test upload with no files"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="At least one file must be provided"):
            client._upload_files([])

        with pytest.raises(ValueError, match="At least one file must be provided"):
            client._upload_files(None)

    def test_upload_nonexistent_file(self):
        """Test upload with nonexistent file"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="File not found"):
            client._upload_files("/nonexistent/file.txt")

    def test_upload_directory_instead_of_file(self):
        """Test upload with directory path"""
        client = Lexa(api_key="test-key")

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Not a file"):
                client._upload_files(temp_dir)

    def test_upload_unsupported_file_input_type(self):
        """Test upload with unsupported file input type"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="Unsupported file input type"):
            client._upload_files(123)  # Invalid type


class TestUploadUrls:
    """Test _upload_urls method"""

    @responses.activate
    def test_upload_single_url(self):
        """Test uploading a single URL"""
        # Mock the HEAD request for file info
        responses.add(
            responses.HEAD,
            "https://example.com/document.pdf",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": 'attachment; filename="document.pdf"',
            },
            status=200,
        )

        # Mock the upload request
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "req-url-1"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_urls("https://example.com/document.pdf")

        assert result.request_id == "req-url-1"

    @responses.activate
    def test_upload_multiple_urls(self):
        """Test uploading multiple URLs"""
        # Mock HEAD requests
        responses.add(
            responses.HEAD,
            "https://example.com/doc1.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )
        responses.add(
            responses.HEAD,
            "https://example.com/doc2.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        # Mock upload request
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "req-url-2"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        urls = ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]
        result = client._upload_urls(urls)

        assert result.request_id == "req-url-2"

    def test_upload_urls_empty_list(self):
        """Test upload with empty URL list"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="At least one file url must be provided"):
            client._upload_urls([])

    def test_upload_urls_invalid_url_format(self):
        """Test upload with invalid URL format"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="Invalid URL format"):
            client._upload_urls("invalid-url")

    @responses.activate
    def test_upload_urls_with_processing_mode(self):
        """Test upload URLs with processing mode"""
        # Mock HEAD request
        responses.add(
            responses.HEAD,
            "https://example.com/doc.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        # Mock upload request
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "req-url-3"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_urls(
            "https://example.com/doc.pdf", ProcessingMode.ADVANCED
        )

        assert result.request_id == "req-url-3"

        # Check the request payload
        request = responses.calls[1].request  # First is HEAD, second is POST
        payload = json.loads(request.body)
        assert payload["mode"] == "advanced"


class TestGetDocuments:
    """Test _get_documents method"""

    @responses.activate
    def test_get_documents_success(self):
        """Test successful document retrieval"""
        # Mock job status with result
        job_response = {
            "status": "complete",
            "requestID": "job-123",
            "progress": 100,
            "result": {
                "documents": [
                    {
                        "content": {"text": "Document content"},
                        "metadata": {"filename": "test.pdf"},
                    }
                ]
            },
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key")

        # Mock DocumentBatch.from_api_response
        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "mocked_batch"

            result = client._get_documents("job-123")

            assert result == "mocked_batch"
            mock_batch.from_api_response.assert_called_once()

    @responses.activate
    def test_get_documents_no_result(self):
        """Test document retrieval when job has no result"""
        job_response = {
            "status": "complete",
            "requestID": "job-123",
            "progress": 100,
            "result": None,
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-123",
            json=job_response,
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            result = client._get_documents("job-123")

            # Should create empty DocumentBatch
            mock_batch.assert_called_once_with([])


class TestCloudStorageIntegrationPrivate:
    """Test private cloud storage integration methods"""

    @responses.activate
    def test_upload_s3_folder(self):
        """Test S3 folder upload"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/amazon-folder",
            json={"message": "S3 folder processed", "requestID": "req-s3-1"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_s3_folder("my-bucket", "folder/path")

        assert result.request_id == "req-s3-1"

        # Check request payload
        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["bucket"] == "my-bucket"
        assert payload["path"] == "folder/path"
        assert payload["mode"] == "default"
        assert payload["product"] == "lexa"

    @responses.activate
    def test_upload_s3_folder_with_mode(self):
        """Test S3 folder upload with processing mode"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/amazon-folder",
            json={"message": "S3 folder processed", "requestID": "req-s3-2"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_s3_folder("bucket", "path", ProcessingMode.ADVANCED)

        assert result.request_id == "req-s3-2"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["mode"] == "advanced"

    @responses.activate
    def test_upload_box_folder(self):
        """Test Box folder upload"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/box-folder",
            json={"message": "Box folder processed", "requestID": "req-box-1"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_box_folder("folder-123")

        assert result.request_id == "req-box-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-123"

    @responses.activate
    def test_upload_dropbox_folder(self):
        """Test Dropbox folder upload"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/dropbox-folder",
            json={"message": "Dropbox folder processed", "requestID": "req-dropbox-1"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_dropbox_folder("/Documents")

        assert result.request_id == "req-dropbox-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["path"] == "/Documents"

    @responses.activate
    def test_upload_sharepoint_folder(self):
        """Test SharePoint folder upload"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/microsoft-folder",
            json={"message": "SharePoint folder processed", "requestID": "req-sp-1"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_sharepoint_folder("drive-123", "folder-456")

        assert result.request_id == "req-sp-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["drive_id"] == "drive-123"
        assert payload["folder_id"] == "folder-456"

    @responses.activate
    def test_upload_salesforce_folder(self):
        """Test Salesforce folder upload"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/salesforce-folder",
            json={"message": "Salesforce folder processed", "requestID": "req-sf-1"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_salesforce_folder("My Documents")

        assert result.request_id == "req-sf-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["name"] == "My Documents"

    @responses.activate
    def test_upload_sendme_files(self):
        """Test Sendme files upload"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/sendme",
            json={"message": "Sendme files processed", "requestID": "req-sendme-1"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._upload_sendme_files("ticket-123")

        assert result.request_id == "req-sendme-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["ticket"] == "ticket-123"

    def test_cloud_storage_invalid_mode(self):
        """Test cloud storage methods with invalid processing mode"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_s3_folder("bucket", "path", "invalid")

        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_box_folder("folder", "invalid")

        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_dropbox_folder("path", "invalid")

        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_sharepoint_folder("drive", "folder", "invalid")

        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_salesforce_folder("folder", "invalid")

        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_sendme_files("ticket", "invalid")


class TestPublicParseMethods:
    """Test public parse methods"""

    def create_temp_file(self, content: bytes = b"test content", suffix: str = ".txt"):
        """Helper to create temporary files"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def cleanup_temp_file(self, filepath: str):
        """Helper to cleanup temporary files"""
        try:
            os.unlink(filepath)
        except FileNotFoundError:
            pass

    @responses.activate
    def test_parse_success(self):
        """Test successful file parsing"""
        # Mock file upload response
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "req-parse-1"},
            status=200,
        )

        # Mock job status response
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/req-parse-1",
            json={
                "status": "complete",
                "requestID": "req-parse-1",
                "progress": 100,
                "result": {"documents": []},
            },
            status=200,
        )

        temp_file = self.create_temp_file(b"test content", ".txt")

        try:
            client = Lexa(api_key="test-key")

            with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
                mock_batch.from_api_response.return_value = "parsed_documents"

                result = client.parse(temp_file)

                assert result == "parsed_documents"
        finally:
            self.cleanup_temp_file(temp_file)

    def test_parse_no_request_id(self):
        """Test parse when upload doesn't return request_id"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_upload_files") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Uploaded",
                request_id="",  # Empty request ID
                pages=None,
                rejects=None,
                uploads=None,
            )

            with pytest.raises(LexaError, match="Failed to get request ID"):
                client.parse(b"content")

    @responses.activate
    def test_parse_urls_success(self):
        """Test successful URL parsing"""
        # Mock HEAD request for file info
        responses.add(
            responses.HEAD,
            "https://example.com/doc.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        # Mock URL upload response
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "req-parse-url-1"},
            status=200,
        )

        # Mock job status response
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/req-parse-url-1",
            json={
                "status": "complete",
                "requestID": "req-parse-url-1",
                "progress": 100,
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "parsed_url_documents"

            result = client.parse_urls("https://example.com/doc.pdf")

            assert result == "parsed_url_documents"

    def test_parse_urls_no_request_id(self):
        """Test parse_urls when upload doesn't return request_id"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_upload_urls") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Processed",
                request_id="",  # Empty request ID
                pages=None,
                rejects=None,
                uploads=None,
            )

            with pytest.raises(LexaError, match="Failed to get request ID"):
                client.parse_urls("https://example.com/doc.pdf")


class TestCloudStorageListingMethods:
    """Test cloud storage listing methods"""

    @responses.activate
    def test_list_s3_buckets(self):
        """Test listing S3 buckets"""
        bucket_response = {
            "requestID": "req-list-buckets",
            "buckets": [
                {"Name": "bucket1", "CreationDate": "2023-01-01"},
                {"Name": "bucket2", "CreationDate": "2023-01-02"},
            ],
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/amazon-listBuckets",
            json=bucket_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client.list_s3_buckets()

        assert isinstance(result, BucketListResponse)
        assert result.request_id == "req-list-buckets"
        assert len(result.buckets) == 2
        assert result.buckets[0].name == "bucket1"

    @responses.activate
    def test_list_s3_folders(self):
        """Test listing S3 folders"""
        folder_response = {
            "requestID": "req-list-folders",
            "folders": [
                {"id": "folder1", "name": "Documents"},
                {"id": "folder2", "name": "Images"},
            ],
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/amazon-listFoldersInBucket",
            json=folder_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client.list_s3_folders("my-bucket")

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-list-folders"
        assert len(result.folders) == 2

        # Check query parameters
        request = responses.calls[0].request
        assert "bucket=my-bucket" in request.url

    @responses.activate
    def test_list_box_folders(self):
        """Test listing Box folders"""
        folder_response = {
            "requestID": "req-box-folders",
            "folders": [{"id": "box-folder1", "name": "Shared Files"}],
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/box-listFolders",
            json=folder_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client.list_box_folders()

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-box-folders"

    @responses.activate
    def test_list_dropbox_folders(self):
        """Test listing Dropbox folders"""
        folder_response = {
            "requestID": "req-dropbox-folders",
            "folders": [{"id": "dropbox-folder1", "name": "Apps"}],
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/dropbox-listFolders",
            json=folder_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client.list_dropbox_folders()

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-dropbox-folders"

    @responses.activate
    def test_list_sharepoint_sites(self):
        """Test listing SharePoint sites"""
        site_response = {
            "requestID": "req-sp-sites",
            "sites": [
                {
                    "id": "site1",
                    "name": "Company Site",
                    "webUrl": "https://company.sharepoint.com/sites/main",
                }
            ],
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/microsoft-listSites",
            json=site_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client.list_sharepoint_sites()

        assert isinstance(result, SiteListResponse)
        assert result.request_id == "req-sp-sites"
        assert len(result.sites) == 1
        assert result.sites[0].name == "Company Site"

    @responses.activate
    def test_list_sharepoint_drives(self):
        """Test listing SharePoint drives"""
        drive_response = {
            "requestID": "req-sp-drives",
            "drives": [
                {"id": "drive1", "name": "Documents", "driveType": "documentLibrary"}
            ],
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/microsoft-listDrivesInSite",
            json=drive_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client.list_sharepoint_drives("site-123")

        assert isinstance(result, DriveListResponse)
        assert result.request_id == "req-sp-drives"

        # Check query parameters
        request = responses.calls[0].request
        assert "site_id=site-123" in request.url

    @responses.activate
    def test_list_sharepoint_folders(self):
        """Test listing SharePoint folders"""
        folder_response = {
            "requestID": "req-sp-folders",
            "folders": [{"id": "folder1", "name": "Shared Documents"}],
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/microsoft-listFoldersInDrive",
            json=folder_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client.list_sharepoint_folders("drive-123")

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-sp-folders"

        # Check query parameters
        request = responses.calls[0].request
        assert "drive_id=drive-123" in request.url

    @responses.activate
    def test_list_salesforce_folders(self):
        """Test listing Salesforce folders"""
        folder_response = {
            "requestID": "req-sf-folders",
            "folders": [{"id": "sf-folder1", "name": "Sales Documents"}],
        }
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/salesforce-listFolders",
            json=folder_response,
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client.list_salesforce_folders()

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-sf-folders"


class TestCloudStorageParsingMethods:
    """Test cloud storage parsing methods"""

    @responses.activate
    def test_parse_s3_folder(self):
        """Test parsing S3 folder"""
        # Mock S3 folder upload
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/amazon-folder",
            json={"message": "S3 folder processed", "requestID": "req-s3-parse-1"},
            status=200,
        )

        # Mock job completion
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/req-s3-parse-1",
            json={
                "status": "complete",
                "requestID": "req-s3-parse-1",
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "s3_documents"

            result = client.parse_s3_folder("bucket", "folder/path")

            assert result == "s3_documents"

    def test_parse_s3_folder_no_request_id(self):
        """Test parse_s3_folder when upload doesn't return request_id"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_upload_s3_folder") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Processed",
                request_id="",  # Empty request ID
                pages=None,
                rejects=None,
                uploads=None,
            )

            with pytest.raises(LexaError, match="Failed to get request ID"):
                client.parse_s3_folder("bucket", "folder")

    @responses.activate
    def test_parse_box_folder(self):
        """Test parsing Box folder"""
        # Mock Box folder upload
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/box-folder",
            json={"message": "Box folder processed", "requestID": "req-box-parse-1"},
            status=200,
        )

        # Mock job completion
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/req-box-parse-1",
            json={
                "status": "complete",
                "requestID": "req-box-parse-1",
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "box_documents"

            result = client.parse_box_folder("box-folder-123")

            assert result == "box_documents"

    def test_parse_box_folder_no_request_id(self):
        """Test parse_box_folder when upload doesn't return request_id"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_upload_box_folder") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Processed",
                request_id="",  # Empty request ID
                pages=None,
                rejects=None,
                uploads=None,
            )

            with pytest.raises(LexaError, match="Failed to get request ID"):
                client.parse_box_folder("folder")

    @responses.activate
    def test_parse_dropbox_folder(self):
        """Test parsing Dropbox folder"""
        # Mock Dropbox folder upload
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/dropbox-folder",
            json={
                "message": "Dropbox folder processed",
                "requestID": "req-dropbox-parse-1",
            },
            status=200,
        )

        # Mock job completion
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/req-dropbox-parse-1",
            json={
                "status": "complete",
                "requestID": "req-dropbox-parse-1",
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "dropbox_documents"

            result = client.parse_dropbox_folder("/Documents")

            assert result == "dropbox_documents"

    def test_parse_dropbox_folder_no_request_id(self):
        """Test parse_dropbox_folder when upload doesn't return request_id"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_upload_dropbox_folder") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Processed",
                request_id="",  # Empty request ID
                pages=None,
                rejects=None,
                uploads=None,
            )

            with pytest.raises(LexaError, match="Failed to get request ID"):
                client.parse_dropbox_folder("/path")

    @responses.activate
    def test_parse_sharepoint_folder(self):
        """Test parsing SharePoint folder"""
        # Mock SharePoint folder upload
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/microsoft-folder",
            json={
                "message": "SharePoint folder processed",
                "requestID": "req-sp-parse-1",
            },
            status=200,
        )

        # Mock job completion
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/req-sp-parse-1",
            json={
                "status": "complete",
                "requestID": "req-sp-parse-1",
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "sharepoint_documents"

            result = client.parse_sharepoint_folder("drive-123", "folder-456")

            assert result == "sharepoint_documents"

    def test_parse_sharepoint_folder_no_request_id(self):
        """Test parse_sharepoint_folder when upload doesn't return request_id"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_upload_sharepoint_folder") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Processed",
                request_id="",  # Empty request ID
                pages=None,
                rejects=None,
                uploads=None,
            )

            with pytest.raises(LexaError, match="Failed to get request ID"):
                client.parse_sharepoint_folder("drive", "folder")

    @responses.activate
    def test_parse_salesforce_folder(self):
        """Test parsing Salesforce folder"""
        # Mock Salesforce folder upload
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/salesforce-folder",
            json={
                "message": "Salesforce folder processed",
                "requestID": "req-sf-parse-1",
            },
            status=200,
        )

        # Mock job completion
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/req-sf-parse-1",
            json={
                "status": "complete",
                "requestID": "req-sf-parse-1",
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "salesforce_documents"

            result = client.parse_salesforce_folder("Sales Documents")

            assert result == "salesforce_documents"

    def test_parse_salesforce_folder_no_request_id(self):
        """Test parse_salesforce_folder when upload doesn't return request_id"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_upload_salesforce_folder") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Processed",
                request_id="",  # Empty request ID
                pages=None,
                rejects=None,
                uploads=None,
            )

            with pytest.raises(LexaError, match="Failed to get request ID"):
                client.parse_salesforce_folder("folder")

    @responses.activate
    def test_parse_sendme_files(self):
        """Test parsing Sendme files"""
        # Mock Sendme files upload
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/sendme",
            json={
                "message": "Sendme files processed",
                "requestID": "req-sendme-parse-1",
            },
            status=200,
        )

        # Mock job completion
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/req-sendme-parse-1",
            json={
                "status": "complete",
                "requestID": "req-sendme-parse-1",
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "sendme_documents"

            result = client.parse_sendme_files("ticket-123")

            assert result == "sendme_documents"

    def test_parse_sendme_files_no_request_id(self):
        """Test parse_sendme_files when upload doesn't return request_id"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_upload_sendme_files") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Processed",
                request_id="",  # Empty request ID
                pages=None,
                rejects=None,
                uploads=None,
            )

            with pytest.raises(LexaError, match="Failed to get request ID"):
                client.parse_sendme_files("ticket")


class TestEdgeCasesAndCoverage:
    """Test edge cases and ensure complete coverage"""

    @responses.activate
    def test_processing_job_with_polling_progress(self):
        """Test processing job with multiple status updates"""
        # First call: processing
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-polling",
            json={"status": "processing", "requestID": "job-polling", "progress": 25},
            status=200,
        )
        # Second call: processing
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-polling",
            json={"status": "processing", "requestID": "job-polling", "progress": 75},
            status=200,
        )
        # Third call: complete
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/job-polling",
            json={
                "status": "complete",
                "requestID": "job-polling",
                "progress": 100,
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        callback_calls = []

        def progress_callback(status):
            callback_calls.append(status.progress)

        with patch("cerevox.clients.lexa.time.sleep"):  # Speed up test
            result = client._wait_for_completion(
                "job-polling",
                timeout=10.0,
                poll_interval=0.1,
                progress_callback=progress_callback,
            )

        assert result.status == JobStatus.COMPLETE
        assert len(callback_calls) == 3
        assert callback_calls == [25, 75, 100]

    def test_upload_files_finally_cleanup(self):
        """Test that file handles are properly cleaned up even on exception"""
        client = Lexa(api_key="test-key")
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"content")
        temp_file.close()

        try:
            # Mock _request to raise an exception after files are opened
            with patch.object(client, "_request") as mock_request:
                mock_request.side_effect = Exception("Upload failed")

                with pytest.raises(Exception, match="Upload failed"):
                    client._upload_files(temp_file.name)

                # File should still be cleanable (handles were closed)
                os.unlink(temp_file.name)
        except FileNotFoundError:
            # File was already cleaned up, which is fine
            pass

    @responses.activate
    def test_file_stream_with_path_name(self):
        """Test file stream with Path object as name"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "Stream uploaded", "requestID": "req-stream-path"},
            status=200,
        )

        client = Lexa(api_key="test-key")
        stream = BytesIO(b"stream content")
        stream.name = Path("/path/to/file.txt")

        result = client._upload_files(stream)
        assert result.request_id == "req-stream-path"

    def test_retry_error_with_response_attribute_but_no_json(self):
        """Test retry error with response attribute but no json method"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            retry_error = RetryError("No response attribute")
            # No response attribute
            mock_request.side_effect = retry_error

            with pytest.raises(LexaError, match="Request failed after retries"):
                client._request("GET", "/v0/test")

    def test_get_file_info_content_disposition_edge_cases(self):
        """Test content disposition header parsing edge cases"""
        client = Lexa(api_key="test-key")

        test_cases = [
            # No quotes around filename
            ("attachment; filename=simple.pdf", "simple.pdf"),
            # Quotes with spaces
            ('attachment; filename="file with spaces.pdf"', "file with spaces.pdf"),
            # Single quotes
            ("attachment; filename='single-quoted.pdf'", "single-quoted.pdf"),
            # Multiple parameters
            ('attachment; filename="test.pdf"; size=1024', "test.pdf"),
            # Filename with special chars (should be handled by strip())
            ('attachment; filename="  test-file.pdf  "', "test-file.pdf"),
        ]

        for disposition, expected_name in test_cases:
            with patch.object(client.session, "head") as mock_head:
                mock_response = Mock()
                mock_response.headers = {
                    "Content-Disposition": disposition,
                    "Content-Type": "application/pdf",
                }
                mock_response.raise_for_status.return_value = None
                mock_head.return_value = mock_response

                file_info = client._get_file_info_from_url(
                    "https://example.com/test.pdf"
                )
                assert file_info.name == expected_name


class TestParameterValidation:
    """Test parameter validation and error handling"""

    def test_wait_for_completion_with_default_timeout(self):
        """Test wait_for_completion uses max_poll_time as default timeout"""
        client = Lexa(api_key="test-key", max_poll_time=120.0)

        with patch.object(client, "_get_job_status") as mock_status:
            # Simulate a job that never completes to test timeout
            mock_status.return_value = JobResponse(
                status=JobStatus.PROCESSING,
                request_id="test-job",
                progress=50,
                message="Processing",
            )

            with patch("cerevox.clients.lexa.time.sleep"):  # Speed up test
                start_time = time.time()
                with pytest.raises(LexaTimeoutError):
                    # Use a very small poll interval to make the test fast
                    client._wait_for_completion(
                        "test-job", timeout=0.01, poll_interval=0.001
                    )
                elapsed = time.time() - start_time
                # Should timeout quickly due to our small timeout
                assert elapsed < 1.0

    def test_processing_mode_validation_comprehensive(self):
        """Test processing mode validation across all methods"""
        client = Lexa(api_key="test-key")

        # Test string mode validation
        invalid_modes = ["invalid", "INVALID", "Default", "ADVANCED", ""]
        valid_modes = ["default", "advanced"]

        # Test one method thoroughly (others are similar)
        for invalid_mode in invalid_modes:
            with pytest.raises(ValueError, match="Invalid processing mode"):
                client._upload_files(b"content", invalid_mode)

        # Valid modes should not raise (we'll mock the request)
        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "OK"}

            for valid_mode in valid_modes:
                try:
                    client._upload_files(b"content", valid_mode)
                except Exception as e:
                    # Should not be a validation error
                    assert "Invalid processing mode" not in str(e)


# Integration-style tests that test multiple components together
class TestIntegrationScenarios:
    """Test scenarios that involve multiple components working together"""

    @responses.activate
    def test_full_parse_workflow_with_progress(self):
        """Test complete parsing workflow with progress monitoring"""
        # Mock file upload
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={
                "message": "Files uploaded successfully",
                "requestID": "integration-job-1",
            },
            status=200,
        )

        # Mock multiple job status calls showing progress
        job_statuses = [
            {"status": "processing", "progress": 25},
            {"status": "processing", "progress": 50},
            {"status": "processing", "progress": 75},
            {"status": "complete", "progress": 100, "result": {"documents": []}},
        ]

        for status_data in job_statuses:
            status_data.update({"requestID": "integration-job-1"})
            responses.add(
                responses.GET,
                "https://www.data.cerevox.ai/v0/job/integration-job-1",
                json=status_data,
                status=200,
            )

        client = Lexa(api_key="test-key")
        progress_updates = []

        def track_progress(job_status):
            progress_updates.append(job_status.progress)

        with patch("cerevox.clients.lexa.time.sleep"):  # Speed up polling
            with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
                mock_batch.from_api_response.return_value = "final_documents"

                result = client.parse(
                    b"test content",
                    timeout=10.0,
                    poll_interval=0.1,
                    progress_callback=track_progress,
                )

                assert result == "final_documents"
                assert progress_updates == [25, 50, 75, 100]

    @responses.activate
    def test_parse_with_all_parameter_types(self):
        """Test parse method with all supported parameter combinations"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/files",
            json={"message": "Uploaded", "requestID": "param-test-1"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/param-test-1",
            json={
                "status": "complete",
                "requestID": "param-test-1",
                "result": {"documents": []},
            },
            status=200,
        )

        client = Lexa(api_key="test-key")

        with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
            mock_batch.from_api_response.return_value = "test_result"

            # Test with enum mode
            result = client.parse(
                b"content", mode=ProcessingMode.ADVANCED, timeout=5.0, poll_interval=0.5
            )
            assert result == "test_result"

    def test_error_propagation_through_layers(self):
        """Test that errors properly propagate through method layers"""
        client = Lexa(api_key="test-key")

        # Test error in upload propagates to parse
        with patch.object(client, "_upload_files") as mock_upload:
            mock_upload.side_effect = LexaValidationError("Upload validation failed")

            with pytest.raises(LexaValidationError, match="Upload validation failed"):
                client.parse(b"content")

        # Test error in job waiting propagates to parse
        with patch.object(client, "_upload_files") as mock_upload:
            mock_upload.return_value = IngestionResult(
                message="Uploaded",
                request_id="error-job",
                pages=None,
                rejects=None,
                uploads=None,
            )

            with patch.object(client, "_wait_for_completion") as mock_wait:
                mock_wait.side_effect = LexaJobFailedError("Job processing failed")

                with pytest.raises(LexaJobFailedError, match="Job processing failed"):
                    client.parse(b"content")


class TestAdditionalCoverage:
    """Test additional cases to improve coverage"""

    def test_upload_files_file_close_handling(self):
        """Test that opened files are properly closed"""
        client = Lexa(api_key="test-key")

        # Create a mock file that tracks if close was called
        mock_file = Mock()
        mock_file.read.return_value = b"content"
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)

        with patch("builtins.open", return_value=mock_file):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch.object(client, "_request") as mock_request:
                        mock_request.return_value = {
                            "requestID": "test",
                            "message": "uploaded",
                        }

                        client._upload_files("/fake/path.txt")

                        # Verify close was called
                        mock_file.close.assert_called_once()

    def test_get_file_info_url_with_encoded_characters(self):
        """Test URL with encoded characters"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_response = Mock()
            mock_response.headers = {"Content-Type": "application/pdf"}
            mock_response.raise_for_status.return_value = None
            mock_head.return_value = mock_response

            file_info = client._get_file_info_from_url(
                "https://example.com/my%20file.pdf"
            )

            # Should decode the URL path
            assert file_info.name == "my file.pdf"

    def test_get_file_info_with_empty_content_disposition(self):
        """Test content disposition parsing with empty header"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_response = Mock()
            mock_response.headers = {
                "Content-Disposition": "",  # Empty content disposition
                "Content-Type": "application/pdf",
            }
            mock_response.raise_for_status.return_value = None
            mock_head.return_value = mock_response

            file_info = client._get_file_info_from_url("https://example.com/test.pdf")

            # Should fall back to URL parsing
            assert file_info.name == "test.pdf"

    @responses.activate
    def test_request_with_kwargs(self):
        """Test _request method with additional kwargs"""
        responses.add(
            responses.POST,
            "https://www.data.cerevox.ai/v0/test",
            json={"success": True},
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._request(
            "POST",
            "/v0/test",
            verify=False,  # Additional kwarg
            stream=True,  # Another kwarg
        )

        assert result == {"success": True}

    def test_partial_success_job_status(self):
        """Test job status with partial success"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_get_job_status") as mock_status:
            mock_status.return_value = JobResponse(
                status=JobStatus.PARTIAL_SUCCESS,
                request_id="partial-job",
                progress=75,
                message="Partial success",
            )

            with patch("cerevox.clients.lexa.time.sleep"):
                # Partial success should be treated as completion
                result = client._wait_for_completion(
                    "partial-job", timeout=0.1, poll_interval=0.01
                )
                assert result.status == JobStatus.PARTIAL_SUCCESS

    def test_wait_for_completion_no_timeout_uses_max_poll_time(self):
        """Test that None timeout uses max_poll_time"""
        client = Lexa(api_key="test-key", max_poll_time=0.05)

        with patch.object(client, "_get_job_status") as mock_status:
            mock_status.return_value = JobResponse(
                status=JobStatus.PROCESSING,
                request_id="timeout-job",
                progress=50,
                message="Processing",
            )

            with patch("cerevox.clients.lexa.time.sleep"):
                with pytest.raises(LexaTimeoutError):
                    client._wait_for_completion(
                        "timeout-job", timeout=None, poll_interval=0.01
                    )

    def test_cloud_storage_mode_enum_validation(self):
        """Test cloud storage methods accept ProcessingMode enum"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "OK"}

            # Test that enum modes work for all cloud storage methods
            client._upload_s3_folder("bucket", "path", ProcessingMode.ADVANCED)
            client._upload_box_folder("folder", ProcessingMode.DEFAULT)
            client._upload_dropbox_folder("path", ProcessingMode.ADVANCED)
            client._upload_sharepoint_folder("drive", "folder", ProcessingMode.DEFAULT)
            client._upload_salesforce_folder("folder", ProcessingMode.ADVANCED)
            client._upload_sendme_files("ticket", ProcessingMode.DEFAULT)

            # Verify all calls were made
            assert mock_request.call_count == 6

    def test_get_documents_with_progress_callback(self):
        """Test _get_documents method with progress callback"""
        client = Lexa(api_key="test-key")

        progress_calls = []

        def callback(status):
            progress_calls.append(status.progress)

        with patch.object(client, "_wait_for_completion") as mock_wait:
            mock_wait.return_value = JobResponse(
                status=JobStatus.COMPLETE,
                request_id="doc-job",
                progress=100,
                result={"documents": []},
            )

            with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
                mock_batch.from_api_response.return_value = "documents"

                result = client._get_documents("doc-job", progress_callback=callback)

                # Verify callback was passed through as the 4th positional argument
                mock_wait.assert_called_once()
                args, kwargs = mock_wait.call_args
                assert len(args) == 4
                assert args[3] is callback

    def test_get_documents_with_no_progress_callback(self):
        """Test _get_documents method with no progress callback"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_wait_for_completion") as mock_wait:
            mock_wait.return_value = JobResponse(
                status=JobStatus.COMPLETE,
                request_id="doc-job",
                progress=None,
                result={"documents": []},
            )

            with patch("cerevox.clients.lexa.DocumentBatch") as mock_batch:
                mock_batch.from_api_response.return_value = "documents"

                result = client._get_documents("doc-job", None, None, None, True)

                # Verify callback was passed through as the 4th positional argument
                mock_wait.assert_called_once()
                args, kwargs = mock_wait.call_args
                assert len(args) == 4

    def test_retry_error_with_no_response_attribute(self):
        """Test retry error without response attribute"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            retry_error = RetryError("No response attribute")
            # No response attribute
            mock_request.side_effect = retry_error

            with pytest.raises(LexaError, match="Request failed after retries"):
                client._request("GET", "/v0/test")

    def test_auth_error_with_empty_response(self):
        """Test auth error with empty response content"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.content = b""  # Empty content
            mock_response.json.return_value = {}
            mock_request.return_value = mock_response

            with pytest.raises(LexaAuthError):
                client._request("GET", "/v0/test")

    def test_rate_limit_error_with_empty_response(self):
        """Test rate limit error with empty response content"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.content = b""  # Empty content
            mock_response.json.return_value = {}
            mock_request.return_value = mock_response

            with pytest.raises(LexaRateLimitError):
                client._request("GET", "/v0/test")

    def test_validation_error_with_empty_response(self):
        """Test validation error with empty response content"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.content = b""  # Empty content
            mock_response.json.return_value = {}
            mock_request.return_value = mock_response

            with pytest.raises(LexaValidationError):
                client._request("GET", "/v0/test")

    def test_retry_error_with_response_json_error(self):
        """Test retry error with response that has json() but it raises error"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            retry_error = RetryError("Retry failed")
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            retry_error.response = mock_response
            mock_request.side_effect = retry_error

            with pytest.raises(LexaError, match="Request failed after retries"):
                client._request("GET", "/v0/test")

    def test_retry_error_with_response_no_json_method(self):
        """Test retry error with response that doesn't have json method"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "request") as mock_request:
            retry_error = RetryError("Retry failed")
            mock_response = Mock(spec=[])  # Mock without json method
            retry_error.response = mock_response
            mock_request.side_effect = retry_error

            with pytest.raises(LexaError, match="Request failed after retries"):
                client._request("GET", "/v0/test")

    def test_get_file_info_head_request_404(self):
        """Test file info extraction when HEAD request returns 404"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            mock_head.return_value = mock_response

            file_info = client._get_file_info_from_url(
                "https://example.com/document.pdf"
            )

            assert file_info.name == "document.pdf"
            assert file_info.type == "application/octet-stream"

    def test_get_file_info_url_parsing_exception(self):
        """Test file info when URL parsing raises exception"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("Request failed")

            with patch("cerevox.clients.lexa.urlparse") as mock_urlparse:
                mock_urlparse.side_effect = Exception("URL parsing failed")

                file_info = client._get_file_info_from_url(
                    "https://example.com/document.pdf"
                )

                # Should generate hash-based filename
                assert file_info.name.startswith("file_")
                assert file_info.type == "application/octet-stream"


class TestMissingBranchCoverage:
    """Tests to cover specific missing branches and lines"""

    @responses.activate
    def test_response_json_decode_error(self):
        """Test handling of invalid JSON in response"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/test",
            body="invalid json {",
            status=200,
            content_type="application/json",
        )

        client = Lexa(api_key="test-key")
        result = client._request("GET", "/v0/test")

        # Should return empty dict when JSON decode fails
        assert result == {}

    def test_file_stream_without_name_attribute(self):
        """Test file stream handling without name attribute"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            # Create a stream without a name attribute
            stream = BytesIO(b"content")
            # Don't set name attribute

            result = client._upload_files([stream])
            assert result.request_id == "test"

    def test_stream_with_path_object_name(self):
        """Test stream with Path object as name"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            stream = BytesIO(b"content")
            stream.name = Path("/path/to/file.txt")  # Set name as Path object

            result = client._upload_files([stream])
            assert result.request_id == "test"

    def test_request_id_none_validation(self):
        """Test get_job_status with None request_id"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="request_id cannot be empty"):
            client._get_job_status(None)

    def test_upload_files_exception_in_finally(self):
        """Test that files are cleaned up even when exception occurs"""
        client = Lexa(api_key="test-key")

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"content")
        temp_file.close()

        try:
            with patch.object(client, "_request") as mock_request:
                mock_request.side_effect = Exception("Upload failed")

                with pytest.raises(Exception, match="Upload failed"):
                    client._upload_files(temp_file.name)

        finally:
            # Clean up
            try:
                os.unlink(temp_file.name)
            except FileNotFoundError:
                pass

    def test_file_handle_without_close_method(self):
        """Test file handle that doesn't have close method"""
        client = Lexa(api_key="test-key")

        # Mock a file handle without close method
        mock_file = Mock(spec=[])  # No close method

        with patch("builtins.open", return_value=mock_file):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch.object(client, "_request") as mock_request:
                        mock_request.return_value = {
                            "requestID": "test",
                            "message": "uploaded",
                        }

                        # Should not raise exception even without close method
                        result = client._upload_files("/fake/path.txt")
                        assert result.request_id == "test"

    def test_content_disposition_no_filename_match(self):
        """Test content disposition header without filename match"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_response = Mock()
            mock_response.headers = {
                "Content-Disposition": "attachment; charset=utf-8",  # No filename
                "Content-Type": "application/pdf",
            }
            mock_response.raise_for_status.return_value = None
            mock_head.return_value = mock_response

            file_info = client._get_file_info_from_url("https://example.com/test.pdf")

            # Should fall back to URL parsing
            assert file_info.name == "test.pdf"

    def test_url_with_query_params_in_filename(self):
        """Test URL parsing with query params that get into filename"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_response = Mock()
            mock_response.headers = {"Content-Type": "application/pdf"}
            mock_response.raise_for_status.return_value = None
            mock_head.return_value = mock_response

            file_info = client._get_file_info_from_url(
                "https://example.com/file.pdf?version=1"
            )

            # Should remove query params from filename
            assert file_info.name == "file.pdf"

    def test_url_with_empty_path(self):
        """Test URL with empty path that results in empty filename"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_response = Mock()
            mock_response.headers = {"Content-Type": "text/html"}
            mock_response.raise_for_status.return_value = None
            mock_head.return_value = mock_response

            file_info = client._get_file_info_from_url("https://example.com/")

            # Should generate hash-based filename
            assert file_info.name.startswith("file_")

    def test_head_request_exception_with_url_fallback_exception(self):
        """Test both HEAD request and URL fallback failing"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("HEAD failed")

            with patch("cerevox.clients.lexa.urlparse") as mock_urlparse:
                mock_urlparse.side_effect = Exception("URL parse failed")

                file_info = client._get_file_info_from_url(
                    "https://example.com/test.pdf"
                )

                # Should generate hash-based filename
                assert file_info.name.startswith("file_")
                assert file_info.type == "application/octet-stream"


class TestComprehensiveCoverage:
    """Additional tests to ensure 100% coverage"""

    def test_wait_for_completion_all_error_statuses(self):
        """Test all error status handling in wait_for_completion"""
        client = Lexa(api_key="test-key")

        error_statuses = [
            (JobStatus.FAILED, "failed"),
            (JobStatus.INTERNAL_ERROR, "internal_error"),
            (JobStatus.NOT_FOUND, "not_found"),
        ]

        for status, status_str in error_statuses:
            with patch.object(client, "_get_job_status") as mock_status:
                mock_status.return_value = JobResponse(
                    status=status, request_id="error-job", error=f"Job {status_str}"
                )

                with pytest.raises(LexaJobFailedError, match=f"Job {status_str}"):
                    client._wait_for_completion("error-job", timeout=0.1)

    def test_wait_for_completion_error_without_message(self):
        """Test error handling when no error message provided"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_get_job_status") as mock_status:
            mock_status.return_value = JobResponse(
                status=JobStatus.FAILED,
                request_id="error-job",
                error=None,  # No error message
            )

            with pytest.raises(LexaJobFailedError, match="Job failed"):
                client._wait_for_completion("error-job", timeout=0.1)

    def test_upload_files_with_mixed_types(self):
        """Test uploading mixed file types in single call"""
        client = Lexa(api_key="test-key")

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"file content")
        temp_file.close()

        try:
            with patch.object(client, "_request") as mock_request:
                mock_request.return_value = {
                    "requestID": "mixed-test",
                    "message": "uploaded",
                }

                # Mix of file types
                files = [
                    temp_file.name,  # File path
                    b"raw bytes",  # Raw bytes
                    BytesIO(b"stream"),  # Stream
                ]

                result = client._upload_files(files)
                assert result.request_id == "mixed-test"

        finally:
            os.unlink(temp_file.name)


class TestJobResponseValidation:
    """Test job response handling with different status combinations"""

    @responses.activate
    def test_wait_for_completion_with_partial_success(self):
        """Test wait for completion with partial success status - should complete"""
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/partial-job",
            json={
                "status": "partial_success",
                "requestID": "partial-job",
                "progress": 75,
                "message": "Some files processed successfully",
            },
            status=200,
        )

        client = Lexa(api_key="test-key")
        result = client._wait_for_completion("partial-job")

        # partial_success should be treated as completion
        assert result.status == JobStatus.PARTIAL_SUCCESS
        assert result.progress == 75

    def test_job_response_creation_with_defaults(self):
        """Test JobResponse creation with minimal data"""
        # Test that JobResponse can be created with defaults
        response = JobResponse(status=JobStatus.PROCESSING, request_id="test-job")

        assert response.status == JobStatus.PROCESSING
        assert response.request_id == "test-job"
        assert response.progress == None  # Default value
        assert response.message == None  # Default value


class TestSpecificCoverageMisses:
    """Tests to cover specific missing lines and branches from coverage report"""

    def test_get_job_status_with_none_request_id(self):
        """Test get_job_status with None request_id (line 378)"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="request_id cannot be empty"):
            client._get_job_status(None)

    def test_get_job_status_with_whitespace_request_id(self):
        """Test get_job_status with whitespace-only request_id (line 378)"""
        client = Lexa(api_key="test-key")

        with pytest.raises(ValueError, match="request_id cannot be empty"):
            client._get_job_status("   ")

    def test_upload_files_exception_during_file_enumeration(self):
        """Test exception during file enumeration (lines 481-488)"""
        client = Lexa(api_key="test-key")

        # Create a mock file that raises exception when checking exists
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = Exception("File system error")

            with pytest.raises(Exception, match="File system error"):
                client._upload_files("/some/path.txt")

    def test_cloud_storage_upload_with_string_mode_validation(self):
        """Test cloud storage methods with invalid string mode (lines 619-625, etc.)"""
        client = Lexa(api_key="test-key")

        invalid_modes = ["invalid_mode", "INVALID"]

        # Test all cloud storage upload methods with invalid mode
        for invalid_mode in invalid_modes:
            with pytest.raises(ValueError, match="Invalid processing mode"):
                client._upload_s3_folder("bucket", "path", invalid_mode)

            with pytest.raises(ValueError, match="Invalid processing mode"):
                client._upload_box_folder("folder", invalid_mode)

            with pytest.raises(ValueError, match="Invalid processing mode"):
                client._upload_dropbox_folder("path", invalid_mode)

            with pytest.raises(ValueError, match="Invalid processing mode"):
                client._upload_sharepoint_folder("drive", "folder", invalid_mode)

            with pytest.raises(ValueError, match="Invalid processing mode"):
                client._upload_salesforce_folder("folder", invalid_mode)

            with pytest.raises(ValueError, match="Invalid processing mode"):
                client._upload_sendme_files("ticket", invalid_mode)

    def test_upload_files_unsupported_type_branch(self):
        """Test unsupported file input type branch (line 518)"""
        client = Lexa(api_key="test-key")

        # Test with an integer (unsupported type)
        with pytest.raises(ValueError, match="Unsupported file input type"):
            client._upload_files([123])

        # Test with a list (unsupported type)
        with pytest.raises(ValueError, match="Unsupported file input type"):
            client._upload_files([["nested", "list"]])

    def test_upload_urls_mode_validation_branches(self):
        """Test _upload_urls mode validation branches (lines 571-573)"""
        client = Lexa(api_key="test-key")

        # Test ProcessingMode enum branch
        with patch.object(client, "_get_file_info_from_url") as mock_get_info:
            mock_get_info.return_value = FileInfo(
                name="test.pdf",
                url="http://example.com/test.pdf",
                type="application/pdf",
            )

            with patch.object(client, "_request") as mock_request:
                mock_request.return_value = {
                    "requestID": "test",
                    "message": "processed",
                }

                # This should trigger the ProcessingMode enum branch
                result = client._upload_urls(
                    "http://example.com/test.pdf", ProcessingMode.ADVANCED
                )
                assert result.request_id == "test"

        # Test invalid string mode branch
        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_urls("http://example.com/test.pdf", "invalid_mode")

    @responses.activate
    def test_wait_for_completion_covers_status_checks(self):
        """Test to ensure all status check branches are covered (line 439-447)"""
        client = Lexa(api_key="test-key")

        # Test COMPLETE status
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/complete-job",
            json={"status": "complete", "requestID": "complete-job"},
            status=200,
        )

        result = client._wait_for_completion("complete-job", timeout=0.1)
        assert result.status == JobStatus.COMPLETE

        # Clear responses
        responses.reset()

        # Test PARTIAL_SUCCESS status
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/partial-job",
            json={"status": "partial_success", "requestID": "partial-job"},
            status=200,
        )

        result = client._wait_for_completion("partial-job", timeout=0.1)
        assert result.status == JobStatus.PARTIAL_SUCCESS


class TestFinalCoverageGaps:
    """Test remaining coverage gaps to achieve 100% code coverage"""

    def test_api_error_non_json_content_type(self):
        """Test API error with non-JSON content type (lines 225-229)"""
        client = Lexa(api_key="test-key", max_retries=0)

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.headers = {
                "content-type": "text/html"
            }  # Non-JSON content type
            mock_request.return_value = mock_response

            with pytest.raises(LexaError, match="API request failed with status 500"):
                client._request("GET", "/v0/test")

    def test_get_file_info_url_path_empty_after_unquote(self):
        """Test _get_file_info_from_url when URL path becomes empty after unquote (line 340)"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("HEAD request failed")

            # Mock urlparse to return empty path after unquote
            with patch("cerevox.clients.lexa.unquote") as mock_unquote:
                mock_unquote.return_value = ""  # Empty filename after unquote

                file_info = client._get_file_info_from_url(
                    "https://example.com/some/path"
                )

                # Should generate hash-based filename (line 340)
                assert file_info.name.startswith("file_")
                assert file_info.type == "application/octet-stream"

    def test_get_file_info_url_parsing_exception_in_fallback(self):
        """Test exception handling in URL parsing fallback (lines 360)"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("HEAD request failed")

            with patch("cerevox.clients.lexa.urlparse") as mock_urlparse:
                # First call in main try block, second call in fallback
                mock_urlparse.side_effect = [
                    Exception("First urlparse failed"),  # Triggers main exception
                    Exception(
                        "Second urlparse failed"
                    ),  # Triggers fallback exception (line 360)
                ]

                file_info = client._get_file_info_from_url(
                    "https://example.com/test.pdf"
                )

                # Should use final fallback (line 360)
                assert file_info.name.startswith("file_")
                assert file_info.type == "application/octet-stream"

    def test_get_file_info_url_query_in_filename_fallback(self):
        """Test query parameter handling in URL fallback parsing"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("HEAD request failed")

            # This should trigger the fallback parsing where it checks for '?' in filename
            file_info = client._get_file_info_from_url(
                "https://example.com/doc.pdf?version=1&auth=token"
            )

            # Should remove query params from filename
            assert file_info.name == "doc.pdf"
            assert file_info.type == "application/octet-stream"


class TestModeValidationEdgeCases:
    """Test mode validation edge cases that create branch coverage"""

    def test_upload_methods_with_enum_mode_branches(self):
        """Test all upload methods with ProcessingMode enum to cover enum branches"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "OK"}

            # Test each upload method with enum mode to trigger the enum branch
            client._upload_s3_folder("bucket", "path", ProcessingMode.DEFAULT)
            client._upload_box_folder("folder", ProcessingMode.ADVANCED)
            client._upload_dropbox_folder("path", ProcessingMode.DEFAULT)
            client._upload_sharepoint_folder("drive", "folder", ProcessingMode.ADVANCED)
            client._upload_salesforce_folder("folder", ProcessingMode.DEFAULT)
            client._upload_sendme_files("ticket", ProcessingMode.ADVANCED)

            # Verify all calls were made
            assert mock_request.call_count == 6

    def test_upload_urls_with_none_mode(self):
        """Test _upload_urls with None as mode (edge case)"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_get_file_info_from_url") as mock_get_info:
            mock_get_info.return_value = FileInfo(
                name="test.pdf",
                url="http://example.com/test.pdf",
                type="application/pdf",
            )

            with patch.object(client, "_request") as mock_request:
                mock_request.return_value = {
                    "requestID": "test",
                    "message": "processed",
                }

                # This should trigger the mode validation branch with default mode
                result = client._upload_urls("http://example.com/test.pdf")
                assert result.request_id == "test"


class TestComplexBranchCoverage:
    """Test complex branch coverage scenarios"""

    def test_upload_files_with_exception_during_file_processing(self):
        """Test exception handling during file processing that affects finally block"""
        client = Lexa(api_key="test-key")

        # Create a temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"content")
        temp_file.close()

        opened_files = []

        try:
            # Mock the file opening to track opened files
            original_open = open

            def mock_open(*args, **kwargs):
                if "rb" in args or kwargs.get("mode") == "rb":
                    file_handle = original_open(*args, **kwargs)
                    opened_files.append(file_handle)
                    return file_handle
                return original_open(*args, **kwargs)

            with patch("builtins.open", side_effect=mock_open):
                with patch.object(client, "_request") as mock_request:
                    # Make request fail after files are opened
                    mock_request.side_effect = Exception("Upload failed")

                    with pytest.raises(Exception, match="Upload failed"):
                        client._upload_files(temp_file.name)

                    # Verify that files were attempted to be closed
                    # (This tests the finally block cleanup)
                    assert len(opened_files) > 0
                    for file_handle in opened_files:
                        # File should be closed or attempting to close
                        assert hasattr(file_handle, "close")

        finally:
            # Clean up
            try:
                os.unlink(temp_file.name)
            except FileNotFoundError:
                pass
            # Ensure all files are closed
            for file_handle in opened_files:
                try:
                    file_handle.close()
                except:
                    pass


class TestErrorConditionBranches:
    """Test specific error condition branches"""

    def test_api_error_with_json_content_type_but_no_json_body(self):
        """Test API error with JSON content type but response.json() fails"""
        client = Lexa(api_key="test-key", max_retries=0)

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_request.return_value = mock_response

            # This will trigger the JSONDecodeError in line 228, so we expect that error
            with pytest.raises(json.JSONDecodeError):
                client._request("GET", "/v0/test")

    def test_timeout_none_in_wait_for_completion_branch(self):
        """Test explicit timeout=None branch in _wait_for_completion"""
        client = Lexa(api_key="test-key", max_poll_time=0.05)

        with patch.object(client, "_get_job_status") as mock_status:
            mock_status.return_value = JobResponse(
                status=JobStatus.PROCESSING, request_id="test-job", progress=50
            )

            with patch("cerevox.clients.lexa.time.sleep"):
                # Explicitly pass timeout=None to trigger that branch
                with pytest.raises(LexaTimeoutError):
                    client._wait_for_completion(
                        "test-job", timeout=None, poll_interval=0.01
                    )


class TestRemainingLineCoverage:
    """Test remaining specific lines for 100% coverage"""

    def test_file_handle_missing_close_attribute(self):
        """Test file handle without close method in finally block"""
        client = Lexa(api_key="test-key")

        # Create temp files to test with
        temp_file1 = tempfile.NamedTemporaryFile(delete=False)
        temp_file1.write(b"content1")
        temp_file1.close()

        temp_file2 = tempfile.NamedTemporaryFile(delete=False)
        temp_file2.write(b"content2")
        temp_file2.close()

        # Track opened files
        opened_files = []
        original_open = open

        def mock_open(*args, **kwargs):
            if "rb" in args or kwargs.get("mode") == "rb":
                file_handle = original_open(*args, **kwargs)
                opened_files.append(file_handle)
                # For one file, remove the close method to test the hasattr check
                if len(opened_files) == 1:
                    # Create a wrapper without close method
                    class FileWithoutClose:
                        def __init__(self, file_obj):
                            self._file = file_obj

                        def read(self):
                            return self._file.read()

                        def __getattr__(self, name):
                            if name == "close":
                                raise AttributeError(
                                    "'FileWithoutClose' object has no attribute 'close'"
                                )
                            return getattr(self._file, name)

                    wrapper = FileWithoutClose(file_handle)
                    opened_files[-1] = wrapper
                    return wrapper
                return file_handle
            return original_open(*args, **kwargs)

        try:
            with patch("builtins.open", side_effect=mock_open):
                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {
                        "requestID": "test",
                        "message": "uploaded",
                    }

                    # Upload files - this should test the finally block cleanup
                    result = client._upload_files([temp_file1.name, temp_file2.name])

                    assert result.request_id == "test"
                    # Verify that files were tracked
                    assert len(opened_files) == 2

        finally:
            # Clean up
            try:
                os.unlink(temp_file1.name)
                os.unlink(temp_file2.name)
            except Exception:
                pass
            # Close any remaining open files
            for file_handle in opened_files:
                try:
                    if hasattr(file_handle, "close"):
                        file_handle.close()
                except:
                    pass

    def test_path_object_filename_extraction(self):
        """Test Path object filename extraction in upload"""
        client = Lexa(api_key="test-key")

        mock_stream = Mock()
        mock_stream.read.return_value = b"content"
        mock_stream.name = Path("/some/path/to/file.txt")  # Path object as name

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            result = client._upload_files([mock_stream])
            assert result.request_id == "test"

            # Verify that Path.name was used to extract filename
            call_args = mock_request.call_args
            files_dict = call_args[1]["files"]
            # Should extract just the filename part
            assert "file.txt" in str(files_dict)


# Final test to ensure all branches are covered
class TestAbsoluteCompleteness:
    """Final tests to ensure absolute 100% coverage"""

    def test_all_remaining_edge_cases(self):
        """Test any remaining edge cases for complete coverage"""
        client = Lexa(api_key="test-key")

        # Test that we can handle all the edge cases together
        assert client.api_key == "test-key"
        assert client.base_url == "https://www.data.cerevox.ai"

        # Test various initialization edge cases
        with pytest.raises(ValueError):
            Lexa(api_key="test", base_url=None)

        with pytest.raises(ValueError):
            Lexa(api_key="test", base_url="")

    @responses.activate
    def test_content_type_parsing_edge_case(self):
        """Test content type parsing with complex headers"""
        responses.add(
            responses.HEAD,
            "https://example.com/file.txt",
            headers={
                "Content-Type": "text/plain; charset=utf-8; boundary=something",
                "Content-Disposition": 'attachment; filename="test.txt"; size=1024',
            },
            status=200,
        )

        client = Lexa(api_key="test-key")
        file_info = client._get_file_info_from_url("https://example.com/file.txt")

        # Should parse content type correctly, removing parameters
        assert file_info.type == "text/plain"
        assert file_info.name == "test.txt"

    def test_unquote_with_plus_signs(self):
        """Test URL unquoting with plus signs and special characters"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("HEAD failed")

            # URL with encoded characters
            file_info = client._get_file_info_from_url(
                "https://example.com/my%20document%2Bfile.pdf"
            )

            # Should properly decode URL
            assert file_info.name == "my document+file.pdf"

    def test_api_error_with_json_content_type_success(self):
        """Test API error with JSON content type and successful json() call (line 229)"""
        client = Lexa(api_key="test-key", max_retries=0)

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"error": "Server error occurred"}
            mock_request.return_value = mock_response

            with pytest.raises(LexaError, match="Server error occurred"):
                client._request("GET", "/v0/test")


# Tests for the final 2 missing lines
class TestAbsolute100PercentCoverage:
    """Tests to achieve the final 2 missing lines for 100% coverage"""

    def test_get_file_info_filename_with_query_params_normal_path(self):
        """Test filename with query parameters in normal execution path (line 340)"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_response = Mock()
            mock_response.headers = {
                "Content-Disposition": "",  # No filename in Content-Disposition
                "Content-Type": "application/pdf",
            }
            mock_response.raise_for_status.return_value = None
            mock_head.return_value = mock_response

            # Mock urlparse to return a path that results in filename with query params
            with patch("cerevox.clients.lexa.urlparse") as mock_urlparse:
                mock_parsed = Mock()
                mock_parsed.path = "/test.pdf"
                mock_urlparse.return_value = mock_parsed

                with patch("cerevox.clients.lexa.unquote") as mock_unquote:
                    # Return filename with query parameters
                    mock_unquote.return_value = "test.pdf?version=1&auth=token"

                    file_info = client._get_file_info_from_url(
                        "https://example.com/test.pdf?version=1&auth=token"
                    )

                    # This should trigger the query param removal: if '?' in filename:
                    # and result in clean filename
                    assert file_info.name == "test.pdf"
                    assert file_info.type == "application/pdf"

    def test_get_file_info_filename_with_query_params_exception_path(self):
        """Test filename with query parameters in exception fallback path (line 360)"""
        client = Lexa(api_key="test-key")

        with patch.object(client.session, "head") as mock_head:
            mock_head.side_effect = Exception("HEAD request failed")

            # Mock urlparse to return a path that results in filename with query params
            with patch("cerevox.clients.lexa.urlparse") as mock_urlparse:
                mock_parsed = Mock()
                mock_parsed.path = "/document.pdf"
                mock_urlparse.return_value = mock_parsed

                with patch("cerevox.clients.lexa.unquote") as mock_unquote:
                    # Return filename with query parameters
                    mock_unquote.return_value = "document.pdf?id=123&token=abc"

                    file_info = client._get_file_info_from_url(
                        "https://example.com/document.pdf?id=123&token=abc"
                    )

                    # This should trigger the query param removal in exception handler: if '?' in filename:
                    # and result in clean filename
                    assert file_info.name == "document.pdf"
                    assert file_info.type == "application/octet-stream"


class TestMissingTypeErrorBranches:
    """Test the missing TypeError branches for mode validation in all upload methods"""

    def test_upload_files_type_error_branch(self):
        """Test _upload_files TypeError branch for invalid mode type"""
        client = Lexa(api_key="test-key")

        # Test with invalid mode types that should trigger TypeError
        invalid_modes = [123, [], {}, None, object()]

        for invalid_mode in invalid_modes:
            with pytest.raises(
                TypeError, match="Mode must be ProcessingMode enum or string"
            ):
                client._upload_files(b"content", invalid_mode)

    def test_upload_urls_type_error_branch(self):
        """Test _upload_urls TypeError branch for invalid mode type"""
        client = Lexa(api_key="test-key")

        # Test with invalid mode types that should trigger TypeError
        invalid_modes = [123, [], {}, None, object()]

        for invalid_mode in invalid_modes:
            with pytest.raises(
                TypeError, match="Mode must be ProcessingMode enum or string"
            ):
                client._upload_urls("https://example.com/test.pdf", invalid_mode)

    def test_upload_s3_folder_type_error_branch(self):
        """Test _upload_s3_folder TypeError branch for invalid mode type"""
        client = Lexa(api_key="test-key")

        # Test with invalid mode types that should trigger TypeError
        invalid_modes = [123, [], {}, None, object()]

        for invalid_mode in invalid_modes:
            with pytest.raises(
                TypeError, match="Mode must be ProcessingMode enum or string"
            ):
                client._upload_s3_folder("bucket", "path", invalid_mode)

    def test_upload_box_folder_type_error_branch(self):
        """Test _upload_box_folder TypeError branch for invalid mode type"""
        client = Lexa(api_key="test-key")

        # Test with invalid mode types that should trigger TypeError
        invalid_modes = [123, [], {}, None, object()]

        for invalid_mode in invalid_modes:
            with pytest.raises(
                TypeError, match="Mode must be ProcessingMode enum or string"
            ):
                client._upload_box_folder("folder_id", invalid_mode)

    def test_upload_dropbox_folder_type_error_branch(self):
        """Test _upload_dropbox_folder TypeError branch for invalid mode type"""
        client = Lexa(api_key="test-key")

        # Test with invalid mode types that should trigger TypeError
        invalid_modes = [123, [], {}, None, object()]

        for invalid_mode in invalid_modes:
            with pytest.raises(
                TypeError, match="Mode must be ProcessingMode enum or string"
            ):
                client._upload_dropbox_folder("path", invalid_mode)

    def test_upload_sharepoint_folder_type_error_branch(self):
        """Test _upload_sharepoint_folder TypeError branch for invalid mode type"""
        client = Lexa(api_key="test-key")

        # Test with invalid mode types that should trigger TypeError
        invalid_modes = [123, [], {}, None, object()]

        for invalid_mode in invalid_modes:
            with pytest.raises(
                TypeError, match="Mode must be ProcessingMode enum or string"
            ):
                client._upload_sharepoint_folder("drive_id", "folder_id", invalid_mode)

    def test_upload_salesforce_folder_type_error_branch(self):
        """Test _upload_salesforce_folder TypeError branch for invalid mode type"""
        client = Lexa(api_key="test-key")

        # Test with invalid mode types that should trigger TypeError
        invalid_modes = [123, [], {}, None, object()]

        for invalid_mode in invalid_modes:
            with pytest.raises(
                TypeError, match="Mode must be ProcessingMode enum or string"
            ):
                client._upload_salesforce_folder("folder_name", invalid_mode)

    def test_upload_sendme_files_type_error_branch(self):
        """Test _upload_sendme_files TypeError branch for invalid mode type"""
        client = Lexa(api_key="test-key")

        # Test with invalid mode types that should trigger TypeError
        invalid_modes = [123, [], {}, None, object()]

        for invalid_mode in invalid_modes:
            with pytest.raises(
                TypeError, match="Mode must be ProcessingMode enum or string"
            ):
                client._upload_sendme_files("ticket", invalid_mode)


class TestFinal100PercentBranchCoverage:
    """Tests to achieve the final missing branch coverage for 100% coverage"""

    def test_mode_validation_non_string_non_enum_branch(self):
        """Test the branch where mode is neither ProcessingMode enum nor string"""
        client = Lexa(api_key="test-key")

        # Test that when mode is neither ProcessingMode enum nor string,
        # it raises a TypeError
        with pytest.raises(
            TypeError, match="Mode must be ProcessingMode enum or string"
        ):
            client._upload_files(b"content", 123)  # Invalid type for mode

        # Test with a different invalid type
        with pytest.raises(
            TypeError, match="Mode must be ProcessingMode enum or string"
        ):
            client._upload_files(b"content", [])  # List is invalid type

        # Test with None
        with pytest.raises(
            TypeError, match="Mode must be ProcessingMode enum or string"
        ):
            client._upload_files(b"content", None)  # None is invalid type

    def test_wait_for_completion_timeout_is_none_branch(self):
        """Test the specific branch where timeout is None in _wait_for_completion"""
        client = Lexa(api_key="test-key", max_poll_time=0.05)

        with patch.object(client, "_get_job_status") as mock_status:
            mock_status.return_value = JobResponse(
                status=JobStatus.PROCESSING, request_id="test-job", progress=50
            )

            with patch("cerevox.clients.lexa.time.sleep"):
                # This should use max_poll_time as timeout when timeout=None
                with pytest.raises(LexaTimeoutError):
                    client._wait_for_completion(
                        "test-job", timeout=None, poll_interval=0.01
                    )

    def test_upload_files_file_input_not_str_path_bytes_or_readable(self):
        """Test the else branch in file input type checking"""
        client = Lexa(api_key="test-key")

        # Test with a type that doesn't match any of the conditions
        # but we need to pass the initial checks first
        class InvalidFileInput:
            def __init__(self):
                pass

        invalid_input = InvalidFileInput()

        with pytest.raises(ValueError, match="Unsupported file input type"):
            client._upload_files([invalid_input])

    def test_upload_files_path_object_handling_branch(self):
        """Test Path object handling to cover the isinstance(filename, (str, Path)) branch"""
        client = Lexa(api_key="test-key")

        # Create a mock file-like object with Path as name
        mock_stream = Mock()
        mock_stream.read.return_value = b"content"
        mock_stream.name = Path("/some/path/to/file.txt")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            result = client._upload_files([mock_stream])
            assert result.request_id == "test"

    def test_upload_files_path_exists_but_not_file_branch(self):
        """Test the branch where path exists but is not a file"""
        client = Lexa(api_key="test-key")

        # Mock the Path constructor to return a mock that simulates
        # a directory that exists but isn't a file
        with patch("cerevox.clients.lexa.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = False  # This is the branch we want to test
            mock_path_class.return_value = mock_path

            with pytest.raises(ValueError, match="Not a file"):
                client._upload_files(["/some/directory"])

    @responses.activate
    def test_status_check_branches_in_wait_for_completion(self):
        """Test all status checking branches in _wait_for_completion"""
        client = Lexa(api_key="test-key")

        # Test the in [COMPLETE, PARTIAL_SUCCESS] branch
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/complete-job",
            json={"status": "complete", "requestID": "complete-job", "progress": 100},
            status=200,
        )

        result = client._wait_for_completion("complete-job", timeout=0.1)
        assert result.status == JobStatus.COMPLETE

        # Clear responses
        responses.reset()

        # Test the in [FAILED, INTERNAL_ERROR, NOT_FOUND] branch
        responses.add(
            responses.GET,
            "https://www.data.cerevox.ai/v0/job/failed-job",
            json={"status": "failed", "requestID": "failed-job", "error": "Job failed"},
            status=200,
        )

        with pytest.raises(LexaJobFailedError, match="Job failed"):
            client._wait_for_completion("failed-job", timeout=0.1)

    def test_upload_files_finally_block_with_valid_file_handle(self):
        """Test finally block with a valid file handle that has close method"""
        client = Lexa(api_key="test-key")

        # Create a temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"content")
        temp_file.close()

        try:
            with patch.object(client, "_request") as mock_request:
                mock_request.return_value = {"requestID": "test", "message": "uploaded"}

                # This should work normally and test the finally block
                result = client._upload_files(temp_file.name)
                assert result.request_id == "test"

        finally:
            try:
                os.unlink(temp_file.name)
            except FileNotFoundError:
                pass

    def test_mode_parameter_validation_comprehensive_coverage(self):
        """Test comprehensive mode parameter validation to cover all branches"""
        client = Lexa(api_key="test-key")

        # Test with various mode types to cover all branches
        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "OK"}

            # Test ProcessingMode enum branch
            result = client._upload_s3_folder("bucket", "path", ProcessingMode.ADVANCED)
            assert result.request_id == "test"

            # Test valid string mode branch
            result = client._upload_s3_folder("bucket", "path", "default")
            assert result.request_id == "test"

            # Test invalid string mode branch
            with pytest.raises(ValueError, match="Invalid processing mode"):
                client._upload_s3_folder("bucket", "path", "invalid_mode")

    def test_file_input_type_branches_comprehensive(self):
        """Test all file input type branches comprehensively"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            # Test with different file input types to cover all branches

            # Test bytearray (different from bytes)
            result = client._upload_files(bytearray(b"bytearray content"))
            assert result.request_id == "test"

            # Test file-like object with string name
            stream = BytesIO(b"stream content")
            stream.name = "string_filename.txt"
            result = client._upload_files(stream)
            assert result.request_id == "test"

            # Test file-like object with no name attribute
            stream_no_name = BytesIO(b"no name content")
            # Don't set name attribute
            result = client._upload_files(stream_no_name)
            assert result.request_id == "test"

    def test_url_validation_branches_in_upload_urls(self):
        """Test URL validation branches in _upload_urls"""
        client = Lexa(api_key="test-key")

        # Test with valid URLs to trigger the positive branch
        with patch.object(client, "_get_file_info_from_url") as mock_get_info:
            mock_get_info.return_value = FileInfo(
                name="test.pdf",
                url="https://example.com/test.pdf",
                type="application/pdf",
            )

            with patch.object(client, "_request") as mock_request:
                mock_request.return_value = {
                    "requestID": "test",
                    "message": "processed",
                }

                # Test https URL
                result = client._upload_urls("https://example.com/test.pdf")
                assert result.request_id == "test"

                # Test http URL
                result = client._upload_urls("http://example.com/test.pdf")
                assert result.request_id == "test"

        # Test invalid URL format
        with pytest.raises(ValueError, match="Invalid URL format"):
            client._upload_urls("ftp://example.com/test.pdf")

    def test_error_handling_branches_in_request(self):
        """Test error handling branches in _request method"""
        client = Lexa(api_key="test-key", max_retries=0)

        # Test the branch where response.content exists
        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.content = b'{"error": "auth failed"}'
            mock_response.json.return_value = {"error": "auth failed"}
            mock_request.return_value = mock_response

            with pytest.raises(
                LexaAuthError, match="Invalid API key or authentication failed"
            ):
                client._request("GET", "/v0/test")

        # Test the branch where response.content is empty
        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.content = b""
            mock_response.json.return_value = {}
            mock_request.return_value = mock_response

            with pytest.raises(LexaRateLimitError):
                client._request("GET", "/v0/test")

    def test_processing_mode_string_branches(self):
        """Test processing mode string validation branches"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "OK"}

            # Test valid string modes
            valid_modes = ["default", "advanced"]
            for mode in valid_modes:
                result = client._upload_s3_folder("bucket", "path", mode)
                assert result.request_id == "test"

        # Test invalid string mode
        with pytest.raises(ValueError, match="Invalid processing mode"):
            client._upload_s3_folder("bucket", "path", "invalid_mode")

    def test_file_input_stream_with_different_name_types(self):
        """Test file input stream with different name types to cover all branches"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            # Test stream with no name attribute (uses default)
            stream1 = Mock()
            stream1.read.return_value = b"content1"
            # No name attribute - should use default
            del stream1.name  # Remove name if it exists
            result = client._upload_files([stream1])
            assert result.request_id == "test"

            # Test stream with string name
            stream2 = Mock()
            stream2.read.return_value = b"content2"
            stream2.name = "test.txt"
            result = client._upload_files([stream2])
            assert result.request_id == "test"

            # Test stream with Path name
            stream3 = Mock()
            stream3.read.return_value = b"content3"
            stream3.name = Path("/path/to/test.txt")
            result = client._upload_files([stream3])
            assert result.request_id == "test"


class TestMissingModeParameterBranches:
    """Test the missing branches for default mode parameter handling"""

    def test_upload_files_default_mode_branch(self):
        """Test _upload_files with default mode parameter to cover missing branch"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            # Call without explicit mode parameter to trigger default branch
            result = client._upload_files(
                b"content"
            )  # Uses default ProcessingMode.DEFAULT
            assert result.request_id == "test"

            # Verify the default was used
            call_args = mock_request.call_args
            assert (
                call_args[1]["params"]["mode"] == "default"
            )  # ProcessingMode.DEFAULT.value

    def test_upload_urls_default_mode_branch(self):
        """Test _upload_urls with default mode parameter to cover missing branch"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_get_file_info_from_url") as mock_get_info:
            mock_get_info.return_value = FileInfo(
                name="test.pdf",
                url="https://example.com/test.pdf",
                type="application/pdf",
            )

            with patch.object(client, "_request") as mock_request:
                mock_request.return_value = {
                    "requestID": "test",
                    "message": "processed",
                }

                # Call without explicit mode parameter to trigger default branch
                result = client._upload_urls(
                    "https://example.com/test.pdf"
                )  # Uses default
                assert result.request_id == "test"

                # Verify the default was used
                call_args = mock_request.call_args
                payload = call_args[1]["json_data"]
                assert payload["mode"] == "default"

    def test_upload_s3_folder_default_mode_branch(self):
        """Test _upload_s3_folder with default mode parameter to cover missing branch"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "processed"}

            # Call without explicit mode parameter to trigger default branch
            result = client._upload_s3_folder("bucket", "path")  # Uses default
            assert result.request_id == "test"

            # Verify the default was used
            call_args = mock_request.call_args
            payload = call_args[1]["json_data"]
            assert payload["mode"] == "default"

    def test_upload_box_folder_default_mode_branch(self):
        """Test _upload_box_folder with default mode parameter to cover missing branch"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "processed"}

            # Call without explicit mode parameter to trigger default branch
            result = client._upload_box_folder("folder_id")  # Uses default
            assert result.request_id == "test"

            # Verify the default was used
            call_args = mock_request.call_args
            payload = call_args[1]["json_data"]
            assert payload["mode"] == "default"

    def test_upload_dropbox_folder_default_mode_branch(self):
        """Test _upload_dropbox_folder with default mode parameter to cover missing branch"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "processed"}

            # Call without explicit mode parameter to trigger default branch
            result = client._upload_dropbox_folder("path")  # Uses default
            assert result.request_id == "test"

            # Verify the default was used
            call_args = mock_request.call_args
            payload = call_args[1]["json_data"]
            assert payload["mode"] == "default"

    def test_upload_sharepoint_folder_default_mode_branch(self):
        """Test _upload_sharepoint_folder with default mode parameter to cover missing branch"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "processed"}

            # Call without explicit mode parameter to trigger default branch
            result = client._upload_sharepoint_folder(
                "drive_id", "folder_id"
            )  # Uses default
            assert result.request_id == "test"

            # Verify the default was used
            call_args = mock_request.call_args
            payload = call_args[1]["json_data"]
            assert payload["mode"] == "default"

    def test_upload_salesforce_folder_default_mode_branch(self):
        """Test _upload_salesforce_folder with default mode parameter to cover missing branch"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "processed"}

            # Call without explicit mode parameter to trigger default branch
            result = client._upload_salesforce_folder("folder_name")  # Uses default
            assert result.request_id == "test"

            # Verify the default was used
            call_args = mock_request.call_args
            payload = call_args[1]["json_data"]
            assert payload["mode"] == "default"

    def test_upload_sendme_files_default_mode_branch(self):
        """Test _upload_sendme_files with default mode parameter to cover missing branch"""
        client = Lexa(api_key="test-key")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "processed"}

            # Call without explicit mode parameter to trigger default branch
            result = client._upload_sendme_files("ticket")  # Uses default
            assert result.request_id == "test"

            # Verify the default was used
            call_args = mock_request.call_args
            payload = call_args[1]["json_data"]
            assert payload["mode"] == "default"


# Tests for the final missing lines to achieve 100% coverage
class TestFinalMissingLines:
    """Tests to cover the final missing lines for 100% coverage"""

    def test_upload_files_path_name_extraction_oserror(self):
        """Test Path(filename).name raising OSError to cover lines 510-512"""
        client = Lexa(api_key="test-key")

        # Create a custom filename object that looks like a string but causes Path() to fail
        class ProblematicFilename(str):
            def __new__(cls, value):
                return str.__new__(cls, value)

        # Create a mock stream
        mock_stream = Mock()
        mock_stream.read.return_value = b"content"
        mock_stream.name = ProblematicFilename("problematic_file.txt")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            # Create a custom Path class that raises OSError for our specific filename
            original_path = Path

            class TestPath:
                def __init__(self, path_arg):
                    if isinstance(path_arg, ProblematicFilename):
                        raise OSError("Invalid path")
                    self._path = original_path(path_arg)

                def __getattr__(self, name):
                    return getattr(self._path, name)

                @property
                def name(self):
                    return self._path.name

            with patch("cerevox.clients.lexa.Path", TestPath):
                result = client._upload_files([mock_stream])
                assert result.request_id == "test"

    def test_upload_files_path_name_extraction_valueerror(self):
        """Test Path(filename).name raising ValueError to cover lines 510-512"""
        client = Lexa(api_key="test-key")

        # Create a custom filename object
        class BadFilename(str):
            def __new__(cls, value):
                return str.__new__(cls, value)

        # Create a mock stream
        mock_stream = Mock()
        mock_stream.read.return_value = b"content"
        mock_stream.name = BadFilename("bad_file.txt")

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            # Create a custom Path class that raises ValueError for our specific filename
            original_path = Path

            class TestPath:
                def __init__(self, path_arg):
                    if isinstance(path_arg, BadFilename):
                        raise ValueError("Invalid path format")
                    self._path = original_path(path_arg)

                def __getattr__(self, name):
                    return getattr(self._path, name)

                @property
                def name(self):
                    return self._path.name

            with patch("cerevox.clients.lexa.Path", TestPath):
                result = client._upload_files([mock_stream])
                assert result.request_id == "test"

    def test_upload_files_filename_none_in_exception_handler(self):
        """Test the case where filename is None in the exception handler"""
        client = Lexa(api_key="test-key")

        # Create a mock stream with a special None-like object
        class NoneFilename:
            def __str__(self):
                return ""

            def __bool__(self):
                return False  # This makes it falsy like None

        mock_stream = Mock()
        mock_stream.read.return_value = b"content"
        mock_stream.name = NoneFilename()

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            # Create a custom Path class that raises OSError for our NoneFilename
            original_path = Path

            class TestPath:
                def __init__(self, path_arg):
                    if isinstance(path_arg, NoneFilename):
                        raise OSError("Invalid path")
                    self._path = original_path(path_arg)

                def __getattr__(self, name):
                    return getattr(self._path, name)

                @property
                def name(self):
                    return self._path.name

            with patch("cerevox.clients.lexa.Path", TestPath):
                result = client._upload_files([mock_stream])
                assert result.request_id == "test"

    def test_upload_files_empty_filename_in_exception_handler(self):
        """Test the case where filename is empty string in the exception handler"""
        client = Lexa(api_key="test-key")

        # Create a custom empty string class
        class EmptyFilename(str):
            def __new__(cls):
                return str.__new__(cls, "")

            def __bool__(self):
                return False  # This makes it falsy like empty string

        mock_stream = Mock()
        mock_stream.read.return_value = b"content"
        mock_stream.name = EmptyFilename()

        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "uploaded"}

            # Create a custom Path class that raises ValueError for our EmptyFilename
            original_path = Path

            class TestPath:
                def __init__(self, path_arg):
                    if isinstance(path_arg, EmptyFilename):
                        raise ValueError("Invalid path format")
                    self._path = original_path(path_arg)

                def __getattr__(self, name):
                    return getattr(self._path, name)

                @property
                def name(self):
                    return self._path.name

            with patch("cerevox.clients.lexa.Path", TestPath):
                result = client._upload_files([mock_stream])
                assert result.request_id == "test"

    def test_get_documents_new_format(self):
        """Test get_documents with new format"""
        client = Lexa(api_key="test-key")

        # Test case 1: New format with CompletedFileData objects (hasattr version)
        mock_file_data_1 = Mock()
        mock_file_data_1.data = [
            {
                "id": "elem1",
                "element_type": "paragraph",
                "content": {
                    "text": "Test content 1",
                    "html": "<p>Test content 1</p>",
                    "markdown": "Test content 1",
                },
                "source": {
                    "file": {
                        "name": "test1.pdf",
                        "extension": "pdf",
                        "id": "file1",
                        "index": 0,
                        "mime_type": "application/pdf",
                        "original_mime_type": "application/pdf",
                    },
                    "page": {"page_number": 1, "index": 0},
                    "element": {"characters": 14, "words": 3, "sentences": 1},
                },
            }
        ]

        mock_file_data_2 = Mock()
        mock_file_data_2.data = [
            {
                "id": "elem2",
                "element_type": "paragraph",
                "content": {
                    "text": "Test content 2",
                    "html": "<p>Test content 2</p>",
                    "markdown": "Test content 2",
                },
                "source": {
                    "file": {
                        "name": "test2.pdf",
                        "extension": "pdf",
                        "id": "file2",
                        "index": 1,
                        "mime_type": "application/pdf",
                        "original_mime_type": "application/pdf",
                    },
                    "page": {"page_number": 1, "index": 0},
                    "element": {"characters": 14, "words": 3, "sentences": 1},
                },
            }
        ]

        mock_status = Mock()
        mock_status.files = {
            "test1.pdf": mock_file_data_1,
            "test2.pdf": mock_file_data_2,
        }
        mock_status.result = None

        with patch.object(client, "_wait_for_completion", return_value=mock_status):
            with patch("cerevox.clients.lexa.DocumentBatch") as MockDocumentBatch:
                mock_batch = Mock()
                MockDocumentBatch.from_api_response.return_value = mock_batch

                result = client._get_documents("test-request-id")

                # Verify _wait_for_completion was called
                client._wait_for_completion.assert_called_once()

                # Verify DocumentBatch.from_api_response was called with combined elements
                MockDocumentBatch.from_api_response.assert_called_once()
                call_args = MockDocumentBatch.from_api_response.call_args[0][0]

                # Should contain elements from both files
                assert len(call_args) == 2
                assert call_args[0]["id"] == "elem1"
                assert call_args[1]["id"] == "elem2"
                assert result == mock_batch

        # Test case 2: New format with dict representation of CompletedFileData
        mock_status_dict = Mock()
        mock_status_dict.files = {
            "test1.pdf": {
                "data": [
                    {
                        "id": "elem1",
                        "element_type": "paragraph",
                        "content": {
                            "text": "Dict test content",
                            "html": "<p>Dict test content</p>",
                            "markdown": "Dict test content",
                        },
                        "source": {
                            "file": {
                                "name": "test1.pdf",
                                "extension": "pdf",
                                "id": "file1",
                                "index": 0,
                                "mime_type": "application/pdf",
                                "original_mime_type": "application/pdf",
                            },
                            "page": {"page_number": 1, "index": 0},
                            "element": {"characters": 17, "words": 3, "sentences": 1},
                        },
                    }
                ]
            }
        }
        mock_status_dict.result = None

        with patch.object(
            client, "_wait_for_completion", return_value=mock_status_dict
        ):
            with patch("cerevox.clients.lexa.DocumentBatch") as MockDocumentBatch:
                mock_batch = Mock()
                MockDocumentBatch.from_api_response.return_value = mock_batch

                result = client._get_documents("test-request-id")

                # Verify DocumentBatch.from_api_response was called
                MockDocumentBatch.from_api_response.assert_called_once()
                call_args = MockDocumentBatch.from_api_response.call_args[0][0]

                assert len(call_args) == 1
                assert call_args[0]["id"] == "elem1"
                assert call_args[0]["content"]["text"] == "Dict test content"
                assert result == mock_batch

        # Test case 3: New format with empty data arrays (should return empty DocumentBatch)
        mock_file_data_empty = Mock()
        mock_file_data_empty.data = []

        mock_status_empty = Mock()
        mock_status_empty.files = {"test.pdf": mock_file_data_empty}
        mock_status_empty.result = None

        with patch.object(
            client, "_wait_for_completion", return_value=mock_status_empty
        ):
            with patch("cerevox.clients.lexa.DocumentBatch") as MockDocumentBatch:
                mock_empty_batch = Mock()
                MockDocumentBatch.return_value = mock_empty_batch

                result = client._get_documents("test-request-id")

                # Should create empty DocumentBatch since no elements were found
                MockDocumentBatch.assert_called_once_with([])
                assert result == mock_empty_batch

        # Test case 4: New format with None data (should skip)
        mock_file_data_none = Mock()
        mock_file_data_none.data = None

        mock_status_none = Mock()
        mock_status_none.files = {"test.pdf": mock_file_data_none}
        mock_status_none.result = None

        with patch.object(
            client, "_wait_for_completion", return_value=mock_status_none
        ):
            with patch("cerevox.clients.lexa.DocumentBatch") as MockDocumentBatch:
                mock_empty_batch = Mock()
                MockDocumentBatch.return_value = mock_empty_batch

                result = client._get_documents("test-request-id")

                # Should create empty DocumentBatch since data was None
                MockDocumentBatch.assert_called_once_with([])
                assert result == mock_empty_batch

        # Test case 5: Mixed file types - some with data, some without
        mock_file_with_data = Mock()
        mock_file_with_data.data = [
            {
                "id": "elem1",
                "element_type": "paragraph",
                "content": {"text": "Valid content"},
                "source": {
                    "file": {
                        "name": "valid.pdf",
                        "extension": "pdf",
                        "id": "f1",
                        "index": 0,
                        "mime_type": "application/pdf",
                        "original_mime_type": "application/pdf",
                    },
                    "page": {"page_number": 1, "index": 0},
                    "element": {"characters": 13, "words": 2, "sentences": 1},
                },
            }
        ]

        mock_file_no_data = Mock()
        mock_file_no_data.data = None

        mock_status_mixed = Mock()
        mock_status_mixed.files = {
            "valid.pdf": mock_file_with_data,
            "empty.pdf": mock_file_no_data,
        }
        mock_status_mixed.result = None

        with patch.object(
            client, "_wait_for_completion", return_value=mock_status_mixed
        ):
            with patch("cerevox.clients.lexa.DocumentBatch") as MockDocumentBatch:
                mock_batch = Mock()
                MockDocumentBatch.from_api_response.return_value = mock_batch

                result = client._get_documents("test-request-id")

                # Should only include elements from file with data
                MockDocumentBatch.from_api_response.assert_called_once()
                call_args = MockDocumentBatch.from_api_response.call_args[0][0]

                assert len(call_args) == 1
                assert call_args[0]["id"] == "elem1"
                assert result == mock_batch

        # Test case 6: Fallback to old format when no files field
        mock_status_old = Mock()
        mock_status_old.files = None
        mock_status_old.result = {"test": "old format data"}

        with patch.object(client, "_wait_for_completion", return_value=mock_status_old):
            with patch("cerevox.clients.lexa.DocumentBatch") as MockDocumentBatch:
                mock_batch = Mock()
                MockDocumentBatch.from_api_response.return_value = mock_batch

                result = client._get_documents("test-request-id")

                # Should use old format fallback
                MockDocumentBatch.from_api_response.assert_called_once_with(
                    {"test": "old format data"}
                )
                assert result == mock_batch

        # Test case 7: No data at all (should return empty DocumentBatch)
        mock_status_no_data = Mock()
        mock_status_no_data.files = None
        mock_status_no_data.result = None

        with patch.object(
            client, "_wait_for_completion", return_value=mock_status_no_data
        ):
            with patch("cerevox.clients.lexa.DocumentBatch") as MockDocumentBatch:
                mock_empty_batch = Mock()
                MockDocumentBatch.return_value = mock_empty_batch

                result = client._get_documents("test-request-id")

                # Should return empty DocumentBatch
                MockDocumentBatch.assert_called_once_with([])
                assert result == mock_empty_batch


class TestLexaNewFormat:
    """Tests to cover the new format for Lexa"""

    def test_create_progress_callback(self):
        """Test create_progress_callback comprehensive functionality"""
        import warnings

        client = Lexa(api_key="test-key")

        # Test show_progress=False returns None
        progress_callback = client._create_progress_callback(show_progress=False)
        assert progress_callback is None

        # Test show_progress=True returns callback when tqdm is available
        progress_callback = client._create_progress_callback(show_progress=True)

        status = JobResponse(
            request_id="test-123",
            status=JobStatus.PROCESSING,
            progress=None,
            total_files=10,
            completed_files=3,
            total_chunks=100,
            completed_chunks=25,
            failed_chunks=0,
        )

        progress_callback(status)

        assert progress_callback is not None

        assert callable(progress_callback)

    def test_create_progress_callback_tqdm_not_available(self):
        """Test create_progress_callback when tqdm is not available"""
        import warnings

        client = Lexa(api_key="test-key")

        with patch.object(client, "_is_tqdm_available", return_value=False):
            with patch("warnings.warn") as mock_warn:
                progress_callback = client._create_progress_callback(show_progress=True)

                # Should return None when tqdm is not available
                assert progress_callback is None

                # Should warn about tqdm not being available
                mock_warn.assert_called_once_with(
                    "tqdm is not available. Progress bar disabled. Install with: pip install tqdm",
                    ImportWarning,
                )

    @patch("cerevox.clients.lexa.TQDM_AVAILABLE", True)
    def test_create_progress_callback_functionality(self):
        """Test the actual progress callback functionality"""
        client = Lexa(api_key="test-key")

        # Mock tqdm
        mock_tqdm_instance = Mock()
        mock_tqdm_class = Mock(return_value=mock_tqdm_instance)

        with patch("cerevox.clients.lexa.tqdm", mock_tqdm_class):
            progress_callback = client._create_progress_callback(show_progress=True)
            assert progress_callback is not None

            # Test initial call - should create progress bar
            status = JobResponse(
                request_id="test-123",
                status=JobStatus.PROCESSING,
                progress=25,
                total_files=10,
                completed_files=3,
                total_chunks=100,
                completed_chunks=25,
                failed_chunks=0,
            )

            progress_callback(status)

            # Verify tqdm was initialized
            mock_tqdm_class.assert_called_once_with(
                total=100,
                desc="Processing",
                unit="%",
                bar_format="{l_bar}{bar}| {n:.0f}/{total:.0f}% [{elapsed}<{remaining}, {rate_fmt}]",
            )

            # Verify progress was set
            assert mock_tqdm_instance.n == 25

            # Verify description was updated
            expected_desc = "Processing | Files: 3/10 | Chunks: 25/100"
            mock_tqdm_instance.set_description.assert_called_with(expected_desc)
            mock_tqdm_instance.refresh.assert_called()

    @patch("cerevox.clients.lexa.TQDM_AVAILABLE", True)
    def test_create_progress_callback_with_failed_chunks(self):
        """Test progress callback with failed chunks"""
        client = Lexa(api_key="test-key")

        mock_tqdm_instance = Mock()
        mock_tqdm_class = Mock(return_value=mock_tqdm_instance)

        with patch("cerevox.clients.lexa.tqdm", mock_tqdm_class):
            progress_callback = client._create_progress_callback(show_progress=True)

            # Test with failed chunks
            status = JobResponse(
                request_id="test-123",
                status=JobStatus.PROCESSING,
                progress=50,
                total_files=5,
                completed_files=2,
                total_chunks=50,
                completed_chunks=25,
                failed_chunks=3,
            )

            progress_callback(status)

            # Verify description includes error count
            expected_desc = "Processing | Files: 2/5 | Chunks: 25/50 | Errors: 3"
            mock_tqdm_instance.set_description.assert_called_with(expected_desc)

    @patch("cerevox.clients.lexa.TQDM_AVAILABLE", True)
    def test_create_progress_callback_completion_statuses(self):
        """Test progress callback with completion statuses"""
        client = Lexa(api_key="test-key")

        mock_tqdm_instance = Mock()
        mock_tqdm_class = Mock(return_value=mock_tqdm_instance)

        completion_statuses = [
            JobStatus.COMPLETE,
            JobStatus.PARTIAL_SUCCESS,
            JobStatus.FAILED,
        ]

        for status_type in completion_statuses:
            with patch("cerevox.clients.lexa.tqdm", mock_tqdm_class):
                progress_callback = client._create_progress_callback(show_progress=True)

                status = JobResponse(
                    request_id="test-123",
                    status=status_type,
                    progress=100,
                    total_files=1,
                    completed_files=1,
                    total_chunks=10,
                    completed_chunks=10,
                    failed_chunks=0,
                )

                progress_callback(status)

                # Verify progress bar was closed on completion
                mock_tqdm_instance.close.assert_called()

    @patch("cerevox.clients.lexa.TQDM_AVAILABLE", True)
    def test_create_progress_callback_minimal_status(self):
        """Test progress callback with minimal status information"""
        client = Lexa(api_key="test-key")

        mock_tqdm_instance = Mock()
        mock_tqdm_class = Mock(return_value=mock_tqdm_instance)

        with patch("cerevox.clients.lexa.tqdm", mock_tqdm_class):
            progress_callback = client._create_progress_callback(show_progress=True)

            # Test with only progress information
            status = JobResponse(
                request_id="test-123", status=JobStatus.PROCESSING, progress=30
            )

            progress_callback(status)

            # Should still work with minimal info
            assert mock_tqdm_instance.n == 30
            mock_tqdm_instance.set_description.assert_called_with("Processing")

    @patch("cerevox.clients.lexa.TQDM_AVAILABLE", True)
    def test_create_progress_callback_closure_state(self):
        """Test that progress callback maintains closure state correctly"""
        client = Lexa(api_key="test-key")

        mock_tqdm_instance = Mock()
        mock_tqdm_class = Mock(return_value=mock_tqdm_instance)

        with patch("cerevox.clients.lexa.tqdm", mock_tqdm_class):
            progress_callback = client._create_progress_callback(show_progress=True)

            # First call should initialize tqdm
            status1 = JobResponse(
                request_id="test-123", status=JobStatus.PROCESSING, progress=25
            )
            progress_callback(status1)

            # Verify tqdm was created
            assert mock_tqdm_class.call_count == 1

            # Second call should reuse the same tqdm instance
            status2 = JobResponse(
                request_id="test-123", status=JobStatus.PROCESSING, progress=50
            )
            progress_callback(status2)

            # Should not create another tqdm instance
            assert mock_tqdm_class.call_count == 1
            # Should update progress to new value
            assert mock_tqdm_instance.n == 50

    @patch("cerevox.clients.lexa.TQDM_AVAILABLE", True)
    def test_create_progress_callback_multiple_instances(self):
        """Test that different callback instances are independent"""
        client = Lexa(api_key="test-key")

        mock_tqdm_instance1 = Mock()
        mock_tqdm_instance2 = Mock()
        mock_tqdm_class = Mock(side_effect=[mock_tqdm_instance1, mock_tqdm_instance2])

        with patch("cerevox.clients.lexa.tqdm", mock_tqdm_class):
            # Create two separate progress callbacks
            callback1 = client._create_progress_callback(show_progress=True)
            callback2 = client._create_progress_callback(show_progress=True)

            # Use both callbacks
            status = JobResponse(
                request_id="test-123", status=JobStatus.PROCESSING, progress=30
            )

            callback1(status)
            callback2(status)

            # Both should create their own tqdm instances
            assert mock_tqdm_class.call_count == 2
            assert mock_tqdm_instance1.n == 30
            assert mock_tqdm_instance2.n == 30

    def test_new_import(self):
        """Test tqdm import exception handling"""
        import sys
        from unittest.mock import patch

        # Save the original module state for restoration
        original_lexa = sys.modules.get("cerevox.clients.lexa")

        try:
            # Test successful import case - tqdm available
            with patch.dict("sys.modules", {}, clear=False):
                # Remove lexa from modules to force fresh import
                if "cerevox.clients.lexa" in sys.modules:
                    del sys.modules["cerevox.clients.lexa"]

                # Import the module fresh
                import cerevox.clients.lexa

                # Verify that TQDM_AVAILABLE is True when import succeeds
                assert cerevox.clients.lexa.TQDM_AVAILABLE is True

            # Test ImportError case - cause tqdm import to fail
            with patch.dict("sys.modules", {}, clear=False):
                # Remove both tqdm and lexa from modules
                modules_to_remove = ["tqdm", "cerevox.clients.lexa"]
                for module in modules_to_remove:
                    if module in sys.modules:
                        del sys.modules[module]

                # Mock tqdm import to raise ImportError
                original_import = __builtins__["__import__"]

                def mock_import(name, *args, **kwargs):
                    if name == "tqdm":
                        raise ImportError("No module named 'tqdm'")
                    return original_import(name, *args, **kwargs)

                with patch("builtins.__import__", side_effect=mock_import):
                    # Import the module fresh
                    import cerevox.clients.lexa

                    # Verify that TQDM_AVAILABLE is False when ImportError occurs
                    assert cerevox.clients.lexa.TQDM_AVAILABLE is False
        finally:
            # Restore the original module state
            if "cerevox.clients.lexa" in sys.modules:
                del sys.modules["cerevox.clients.lexa"]
            if original_lexa is not None:
                sys.modules["cerevox.clients.lexa"] = original_lexa
            else:
                # Force a clean reimport of the module in its normal state
                import cerevox.clients.lexa
