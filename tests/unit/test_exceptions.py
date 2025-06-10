"""
Test suite for cerevox.exceptions

Comprehensive tests to achieve 100% code coverage for all exception classes,
their methods, properties, and utility functions.
"""

from typing import Any, Dict

import pytest

from cerevox.exceptions import (
    LexaAuthError,
    LexaError,
    LexaJobFailedError,
    LexaQuotaExceededError,
    LexaRateLimitError,
    LexaServerError,
    LexaTimeoutError,
    LexaUnsupportedFileError,
    LexaValidationError,
    create_error_from_response,
    get_retry_strategy,
)


class TestLexaError:
    """Test base LexaError class"""

    def test_basic_initialization(self):
        """Test basic error initialization"""
        error = LexaError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None
        assert error.request_id is None
        assert error.response_data == {}
        assert error.response is None
        assert not error.retry_suggested

    def test_full_initialization(self):
        """Test error initialization with all parameters"""
        response_data = {"error": "test", "details": "more info"}
        error = LexaError(
            "Test error",
            status_code=400,
            response_data=response_data,
            request_id="req-123",
        )
        assert str(error) == "[400] Test error (Request ID: req-123)"
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.request_id == "req-123"
        assert error.response_data == response_data
        assert error.response == response_data

    def test_backward_compatibility_response_param(self):
        """Test backward compatibility with response parameter"""
        response = {"error": "test"}
        error = LexaError("Test error", response=response)
        assert error.response_data == response
        assert error.response == response

    def test_response_data_takes_precedence(self):
        """Test that response_data takes precedence over response"""
        response_data = {"error": "data"}
        response = {"error": "response"}
        error = LexaError("Test error", response_data=response_data, response=response)
        assert error.response_data == response_data
        assert error.response == response_data

    def test_kwargs_handling(self):
        """Test additional kwargs are set as attributes"""
        error = LexaError("Test error", custom_attr="custom_value")
        assert error.custom_attr == "custom_value"

    def test_str_without_optional_fields(self):
        """Test string representation without status code or request ID"""
        error = LexaError("Simple error")
        assert str(error) == "Simple error"

    def test_str_with_status_code_only(self):
        """Test string representation with status code only"""
        error = LexaError("Error with code", status_code=404)
        assert str(error) == "[404] Error with code"

    def test_str_with_request_id_only(self):
        """Test string representation with request ID only"""
        error = LexaError("Error with ID", request_id="req-456")
        assert str(error) == "Error with ID (Request ID: req-456)"


class TestLexaAuthError:
    """Test LexaAuthError class"""

    def test_default_initialization(self):
        """Test default initialization"""
        error = LexaAuthError()
        assert str(error) == "Authentication failed"
        assert error.message == "Authentication failed"
        assert not error.retry_suggested

    def test_custom_message(self):
        """Test custom message"""
        error = LexaAuthError("Invalid API key")
        assert str(error) == "Invalid API key"
        assert error.message == "Invalid API key"
        assert not error.retry_suggested

    def test_with_additional_params(self):
        """Test with additional parameters"""
        error = LexaAuthError("Auth error", status_code=401, request_id="req-auth")
        assert str(error) == "[401] Auth error (Request ID: req-auth)"
        assert not error.retry_suggested


class TestLexaRateLimitError:
    """Test LexaRateLimitError class"""

    def test_default_initialization(self):
        """Test default initialization"""
        error = LexaRateLimitError()
        assert str(error) == "Rate limit exceeded"
        assert error.message == "Rate limit exceeded"
        assert error.retry_after is None
        assert error.retry_suggested
        assert error.get_retry_delay() == 60  # Default 1 minute

    def test_with_retry_after(self):
        """Test with retry_after parameter"""
        error = LexaRateLimitError("Rate limited", retry_after=120)
        assert error.retry_after == 120
        assert error.get_retry_delay() == 120
        assert error.retry_suggested

    def test_custom_message(self):
        """Test custom message"""
        error = LexaRateLimitError("Too many requests")
        assert str(error) == "Too many requests"
        assert error.retry_suggested


class TestLexaTimeoutError:
    """Test LexaTimeoutError class"""

    def test_default_initialization(self):
        """Test default initialization"""
        error = LexaTimeoutError()
        assert str(error) == "Request timed out"
        assert error.message == "Request timed out"
        assert error.timeout_duration is None
        assert error.retry_suggested

    def test_with_timeout_duration(self):
        """Test with timeout duration"""
        error = LexaTimeoutError("Timeout occurred", timeout_duration=30.5)
        assert error.timeout_duration == 30.5
        assert error.retry_suggested

    def test_custom_message(self):
        """Test custom message"""
        error = LexaTimeoutError("Connection timeout")
        assert str(error) == "Connection timeout"
        assert error.retry_suggested


class TestLexaJobFailedError:
    """Test LexaJobFailedError class"""

    def test_default_initialization(self):
        """Test default initialization"""
        error = LexaJobFailedError()
        assert str(error) == "Processing job failed"
        assert error.message == "Processing job failed"
        assert error.job_id is None
        assert error.failure_reason is None
        assert error.retry_suggested  # Default to retryable

    def test_with_job_details(self):
        """Test with job ID and failure reason"""
        error = LexaJobFailedError(
            "Job failed", job_id="job-123", failure_reason="temporary_error"
        )
        assert error.job_id == "job-123"
        assert error.failure_reason == "temporary_error"
        assert error.retry_suggested

    def test_non_retryable_failure_reasons(self):
        """Test non-retryable failure reasons"""
        non_retryable_reasons = [
            "invalid_file_format",
            "file_corrupted",
            "file_too_large",
            "unsupported_format",
        ]

        for reason in non_retryable_reasons:
            error = LexaJobFailedError(failure_reason=reason)
            assert not error.retry_suggested, f"Should not retry for {reason}"

    def test_retryable_failure_reasons(self):
        """Test retryable failure reasons"""
        retryable_reasons = ["server_busy", "temporary_unavailable", "network_error"]

        for reason in retryable_reasons:
            error = LexaJobFailedError(failure_reason=reason)
            assert error.retry_suggested, f"Should retry for {reason}"

    def test_case_insensitive_failure_reason_check(self):
        """Test case insensitive failure reason checking"""
        error = LexaJobFailedError(failure_reason="INVALID_FILE_FORMAT")
        assert not error.retry_suggested


class TestLexaUnsupportedFileError:
    """Test LexaUnsupportedFileError class"""

    def test_default_initialization(self):
        """Test default initialization"""
        error = LexaUnsupportedFileError()
        assert str(error) == "Unsupported file type"
        assert error.message == "Unsupported file type"
        assert error.file_type is None
        assert error.supported_types == []
        assert not error.retry_suggested

    def test_with_file_details(self):
        """Test with file type and supported types"""
        supported = ["pdf", "docx", "txt"]
        error = LexaUnsupportedFileError(
            "File not supported", file_type="xyz", supported_types=supported
        )
        assert error.file_type == "xyz"
        assert error.supported_types == supported
        assert not error.retry_suggested


class TestLexaValidationError:
    """Test LexaValidationError class"""

    def test_default_initialization(self):
        """Test default initialization"""
        error = LexaValidationError()
        assert str(error) == "Request validation failed"
        assert error.message == "Request validation failed"
        assert error.validation_errors == {}
        assert not error.retry_suggested

    def test_with_validation_errors(self):
        """Test with validation errors"""
        validation_errors = {
            "email": "Invalid email format",
            "age": "Must be a positive integer",
        }
        error = LexaValidationError(
            "Validation failed", validation_errors=validation_errors
        )
        assert error.validation_errors == validation_errors
        assert not error.retry_suggested


class TestLexaQuotaExceededError:
    """Test LexaQuotaExceededError class"""

    def test_default_initialization(self):
        """Test default initialization"""
        error = LexaQuotaExceededError()
        assert str(error) == "Usage quota exceeded"
        assert error.message == "Usage quota exceeded"
        assert error.quota_type is None
        assert error.reset_time is None
        assert not error.retry_suggested  # No reset time

    def test_with_reset_time(self):
        """Test with reset time (should be retryable)"""
        error = LexaQuotaExceededError(
            "Quota exceeded", quota_type="monthly", reset_time="2024-01-01T00:00:00Z"
        )
        assert error.quota_type == "monthly"
        assert error.reset_time == "2024-01-01T00:00:00Z"
        assert error.retry_suggested  # Has reset time

    def test_without_reset_time(self):
        """Test without reset time (should not be retryable)"""
        error = LexaQuotaExceededError(quota_type="lifetime")
        assert not error.retry_suggested  # No reset time


class TestLexaServerError:
    """Test LexaServerError class"""

    def test_default_initialization(self):
        """Test default initialization"""
        error = LexaServerError()
        assert str(error) == "Internal server error"
        assert error.message == "Internal server error"
        assert error.retry_suggested

    def test_custom_message(self):
        """Test custom message"""
        error = LexaServerError("Service unavailable")
        assert str(error) == "Service unavailable"
        assert error.retry_suggested


class TestCreateErrorFromResponse:
    """Test create_error_from_response function"""

    def test_none_response_data(self):
        """Test with None response data"""
        error = create_error_from_response(500, None)
        assert isinstance(error, LexaServerError)
        assert error.message == "Unknown error"
        assert error.status_code == 500
        assert error.response_data == {}

    def test_quota_error_type(self):
        """Test quota error type detection"""
        response_data = {
            "error": "Quota exceeded",
            "error_type": "quota_exceeded",
            "quota_type": "monthly",
            "reset_time": "2024-01-01T00:00:00Z",
        }
        error = create_error_from_response(402, response_data, "req-123")
        assert isinstance(error, LexaQuotaExceededError)
        assert error.quota_type == "monthly"
        assert error.reset_time == "2024-01-01T00:00:00Z"
        assert error.request_id == "req-123"

    def test_job_failed_error_type(self):
        """Test job failed error type detection"""
        response_data = {
            "error": "Job processing failed",
            "error_type": "job_failed",
            "job_id": "job-456",
            "failure_reason": "invalid_file_format",
        }
        error = create_error_from_response(422, response_data)
        assert isinstance(error, LexaJobFailedError)
        assert error.job_id == "job-456"
        assert error.failure_reason == "invalid_file_format"

    def test_file_type_error_type(self):
        """Test file type error type detection"""
        response_data = {
            "error": "File type not supported",
            "error_type": "unsupported_file_type",
            "file_type": "xyz",
            "supported_types": ["pdf", "docx"],
        }
        error = create_error_from_response(415, response_data)
        assert isinstance(error, LexaUnsupportedFileError)
        assert error.file_type == "xyz"
        assert error.supported_types == ["pdf", "docx"]

    def test_unsupported_message_detection(self):
        """Test unsupported file detection by message content"""
        response_data = {
            "error": "This file type is unsupported",
            "file_type": "abc",
            "supported_types": ["txt", "pdf"],
        }
        error = create_error_from_response(400, response_data)
        assert isinstance(error, LexaUnsupportedFileError)
        assert error.file_type == "abc"
        assert error.supported_types == ["txt", "pdf"]

    def test_status_code_401_auth_error(self):
        """Test 401 status code creates auth error"""
        response_data = {"error": "Invalid token"}
        error = create_error_from_response(401, response_data)
        assert isinstance(error, LexaAuthError)
        assert error.message == "Invalid token"
        assert error.status_code == 401

    def test_status_code_403_auth_error(self):
        """Test 403 status code creates auth error"""
        response_data = {"error": "Permission denied"}
        error = create_error_from_response(403, response_data)
        assert isinstance(error, LexaAuthError)
        assert error.message == "Access forbidden: Permission denied"
        assert error.status_code == 403

    def test_status_code_429_rate_limit(self):
        """Test 429 status code creates rate limit error"""
        response_data = {"error": "Too many requests", "retry_after": 300}
        error = create_error_from_response(429, response_data)
        assert isinstance(error, LexaRateLimitError)
        assert error.retry_after == 300
        assert error.status_code == 429

    def test_status_code_400_validation_error(self):
        """Test 400 status code creates validation error"""
        response_data = {
            "error": "Invalid parameters",
            "validation_errors": {"name": "Required field"},
        }
        error = create_error_from_response(400, response_data)
        assert isinstance(error, LexaValidationError)
        assert error.validation_errors == {"name": "Required field"}

    def test_status_code_404_not_found(self):
        """Test 404 status code creates generic error with specific message"""
        response_data = {"error": "User not found"}
        error = create_error_from_response(404, response_data)
        assert isinstance(error, LexaError)
        assert not isinstance(error, LexaValidationError)  # Should be base LexaError
        assert error.message == "Resource not found: User not found"
        assert error.status_code == 404

    def test_status_code_408_timeout_error(self):
        """Test 408 status code creates timeout error"""
        response_data = {"error": "Request timeout", "timeout_duration": 30.0}
        error = create_error_from_response(408, response_data)
        assert isinstance(error, LexaTimeoutError)
        assert error.timeout_duration == 30.0

    def test_status_code_415_unsupported_file(self):
        """Test 415 status code creates unsupported file error"""
        response_data = {
            "error": "Media type not supported",
            "file_type": "gif",
            "supported_types": ["jpg", "png"],
        }
        error = create_error_from_response(415, response_data)
        assert isinstance(error, LexaUnsupportedFileError)
        assert error.file_type == "gif"
        assert error.supported_types == ["jpg", "png"]

    def test_status_code_402_quota_exceeded(self):
        """Test 402 status code creates quota exceeded error"""
        response_data = {
            "error": "Payment required",
            "quota_type": "api_calls",
            "reset_time": "2024-02-01T00:00:00Z",
        }
        error = create_error_from_response(402, response_data)
        assert isinstance(error, LexaQuotaExceededError)
        assert error.quota_type == "api_calls"
        assert error.reset_time == "2024-02-01T00:00:00Z"

    def test_status_code_5xx_server_error(self):
        """Test 5xx status codes create server errors"""
        status_codes = [500, 501, 502, 503, 504]
        for status_code in status_codes:
            response_data = {"error": "Server error"}
            error = create_error_from_response(status_code, response_data)
            assert isinstance(error, LexaServerError)
            assert error.status_code == status_code

    def test_unknown_status_code(self):
        """Test unknown status code creates generic error"""
        response_data = {"error": "Some error"}
        error = create_error_from_response(418, response_data)  # I'm a teapot
        assert isinstance(error, LexaError)
        assert not isinstance(error, (LexaAuthError, LexaServerError))
        assert error.message == "Some error"
        assert error.status_code == 418


class TestGetRetryStrategy:
    """Test get_retry_strategy function"""

    def test_non_retryable_error(self):
        """Test strategy for non-retryable errors"""
        error = LexaAuthError("Auth failed")
        strategy = get_retry_strategy(error)

        expected = {
            "should_retry": False,
            "reason": "Error type not suitable for retry",
            "delay": 0,
            "max_retries": 0,
        }
        assert strategy == expected

    def test_rate_limit_error_strategy(self):
        """Test strategy for rate limit errors"""
        error = LexaRateLimitError("Rate limited", retry_after=120)
        strategy = get_retry_strategy(error)

        expected = {
            "should_retry": True,
            "delay": 120,
            "backoff": "fixed",
            "max_retries": 3,
            "reason": "Rate limit - use fixed delay",
        }
        assert strategy == expected

    def test_rate_limit_error_default_delay(self):
        """Test rate limit error with default delay"""
        error = LexaRateLimitError("Rate limited")  # No retry_after
        strategy = get_retry_strategy(error)

        assert strategy["delay"] == 60  # Default delay
        assert strategy["should_retry"] is True

    def test_timeout_error_strategy(self):
        """Test strategy for timeout errors"""
        error = LexaTimeoutError("Timeout")
        strategy = get_retry_strategy(error)

        expected = {
            "should_retry": True,
            "delay": 5,
            "backoff": "exponential",
            "max_retries": 3,
            "reason": "Timeout - use exponential backoff",
        }
        assert strategy == expected

    def test_server_error_strategy(self):
        """Test strategy for server errors"""
        error = LexaServerError("Server down")
        strategy = get_retry_strategy(error)

        expected = {
            "should_retry": True,
            "delay": 2,
            "backoff": "exponential",
            "max_retries": 5,
            "reason": "Server error - aggressive retry",
        }
        assert strategy == expected

    def test_job_failed_error_strategy(self):
        """Test strategy for job failed errors"""
        error = LexaJobFailedError("Job failed", failure_reason="temporary_error")
        strategy = get_retry_strategy(error)

        expected = {
            "should_retry": True,
            "delay": 10,
            "backoff": "linear",
            "max_retries": 2,
            "reason": "Job failure - limited retry",
        }
        assert strategy == expected

    def test_generic_retryable_error_strategy(self):
        """Test strategy for generic retryable errors"""
        error = LexaQuotaExceededError("Quota exceeded", reset_time="later")
        strategy = get_retry_strategy(error)

        expected = {
            "should_retry": True,
            "delay": 3,
            "backoff": "exponential",
            "max_retries": 3,
            "reason": "General error - standard retry",
        }
        assert strategy == expected


class TestEdgeCases:
    """Test edge cases and integration scenarios"""

    def test_error_inheritance_chain(self):
        """Test that all custom errors inherit from LexaError"""
        error_classes = [
            LexaAuthError,
            LexaRateLimitError,
            LexaTimeoutError,
            LexaJobFailedError,
            LexaUnsupportedFileError,
            LexaValidationError,
            LexaQuotaExceededError,
            LexaServerError,
        ]

        for error_class in error_classes:
            error = error_class("Test")
            assert isinstance(error, LexaError)
            assert isinstance(error, Exception)

    def test_error_with_empty_strings(self):
        """Test errors with empty string parameters"""
        error = LexaJobFailedError("", job_id="", failure_reason="")
        assert error.message == ""
        assert error.job_id == ""
        assert error.failure_reason == ""
        assert error.retry_suggested  # Empty string should be retryable

    def test_create_error_with_empty_response(self):
        """Test create_error_from_response with empty response data"""
        error = create_error_from_response(500, {})
        assert isinstance(error, LexaServerError)
        assert error.message == "Unknown error"
        assert error.response_data == {}

    def test_multiple_failure_reasons_in_job_error(self):
        """Test job error with multiple non-retryable keywords"""
        error = LexaJobFailedError(
            failure_reason="file is corrupted and has invalid_file_format"
        )
        assert not error.retry_suggested  # Should catch any non-retryable reason

    def test_case_variations_in_error_types(self):
        """Test case variations in error_type detection"""
        test_cases = [
            ("QUOTA_EXCEEDED", LexaQuotaExceededError),
            ("Job_Failed", LexaJobFailedError),
            ("file_TYPE", LexaUnsupportedFileError),
        ]

        for error_type, expected_class in test_cases:
            response_data = {"error": "Test error", "error_type": error_type}
            error = create_error_from_response(400, response_data)
            assert isinstance(error, expected_class)
