"""
Exception handling for Cerevox SDK

Provides error handling with specific exception types,
detailed error messages, and retry guidance.
"""

from typing import Any, Dict, List, Optional


class LexaError(Exception):
    """
    Base exception for all Cerevox Lexa API errors
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,  # For backward compatibility
        **kwargs: Any,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.status_code: Optional[int] = status_code
        self.request_id: Optional[str] = request_id

        # Handle response_data vs response parameter compatibility
        if response_data is not None:
            self.response_data: Dict[str, Any] = response_data
            self.response: Optional[Dict[str, Any]] = response_data
        elif response is not None:
            self.response_data = response
            self.response = response
        else:
            self.response_data = {}
            self.response = None  # Preserve None for backward compatibility

        # Handle any additional kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        error_msg = self.message
        if self.status_code:
            error_msg = f"[{self.status_code}] {error_msg}"
        if self.request_id:
            error_msg = f"{error_msg} (Request ID: {self.request_id})"
        return error_msg

    @property
    def retry_suggested(self) -> bool:
        """Whether this error suggests retrying the request"""
        return False


class LexaAuthError(LexaError):
    """
    Authentication/authorization error

    Raised when API key is invalid, expired, or lacks permissions.
    """

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)

    @property
    def retry_suggested(self) -> bool:
        return False  # Don't retry auth errors


class LexaRateLimitError(LexaError):
    """
    Rate limit exceeded error

    Includes retry guidance with backoff recommendations.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after: Optional[int] = retry_after

    @property
    def retry_suggested(self) -> bool:
        return True

    def get_retry_delay(self) -> int:
        """Get recommended retry delay in seconds"""
        if self.retry_after:
            return self.retry_after
        return 60  # Default 1 minute backoff


class LexaTimeoutError(LexaError):
    """
    Request timeout error

    Raised when requests take too long or polling times out.
    """

    def __init__(
        self,
        message: str = "Request timed out",
        timeout_duration: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.timeout_duration: Optional[float] = timeout_duration

    @property
    def retry_suggested(self) -> bool:
        return True


class LexaJobFailedError(LexaError):
    """
    Processing job failed error

    Raised when document processing fails on the server side.
    """

    def __init__(
        self,
        message: str = "Processing job failed",
        job_id: Optional[str] = None,
        failure_reason: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.job_id: Optional[str] = job_id
        self.failure_reason: Optional[str] = failure_reason

    @property
    def retry_suggested(self) -> bool:
        # Some job failures can be retried (temporary server issues)
        # Others cannot (invalid file format, corrupted file)
        if self.failure_reason:
            non_retryable = [
                "invalid_file_format",
                "file_corrupted",
                "file_too_large",
                "unsupported_format",
            ]
            return not any(
                reason in self.failure_reason.lower() for reason in non_retryable
            )
        return True  # Default to retryable


class LexaUnsupportedFileError(LexaError):
    """
    Unsupported file type error

    Raised when attempting to process unsupported file formats.
    """

    def __init__(
        self,
        message: str = "Unsupported file type",
        file_type: Optional[str] = None,
        supported_types: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.file_type: Optional[str] = file_type
        self.supported_types: List[str] = supported_types or []

    @property
    def retry_suggested(self) -> bool:
        return False  # File type won't change on retry


class LexaValidationError(LexaError):
    """
    Request validation error

    Raised when request parameters are invalid.
    """

    def __init__(
        self,
        message: str = "Request validation failed",
        validation_errors: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.validation_errors: Dict[str, str] = validation_errors or {}

    @property
    def retry_suggested(self) -> bool:
        return False  # Validation errors need parameter fixes


class LexaQuotaExceededError(LexaError):
    """
    Usage quota exceeded error

    Raised when account limits are reached.
    """

    def __init__(
        self,
        message: str = "Usage quota exceeded",
        quota_type: Optional[str] = None,
        reset_time: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.quota_type: Optional[str] = quota_type
        self.reset_time: Optional[str] = reset_time

    @property
    def retry_suggested(self) -> bool:
        return bool(self.reset_time)  # Can retry after reset time


class LexaServerError(LexaError):
    """
    Server-side error

    Raised for 5xx HTTP status codes.
    """

    def __init__(self, message: str = "Internal server error", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)

    @property
    def retry_suggested(self) -> bool:
        return True  # Server errors are typically retryable


def create_error_from_response(
    status_code: int,
    response_data: Optional[Dict[str, Any]],
    request_id: Optional[str] = None,
) -> LexaError:
    """
    Create appropriate exception from HTTP response

    This provides intelligent error classification that competitors lack.
    """
    if response_data is None:
        response_data = {}

    message = response_data.get("error", "Unknown error")
    error_type = response_data.get("error_type", "")

    base_kwargs: Dict[str, Any] = {
        "status_code": status_code,
        "response_data": response_data,
        "request_id": request_id,
    }

    # Check error_type first for specific error classifications
    if "quota" in error_type.lower():
        quota_type = response_data.get("quota_type")
        reset_time = response_data.get("reset_time")
        return LexaQuotaExceededError(
            message, quota_type=quota_type, reset_time=reset_time, **base_kwargs
        )

    if "job_failed" in error_type.lower():
        job_id = response_data.get("job_id")
        failure_reason = response_data.get("failure_reason")
        return LexaJobFailedError(
            message, job_id=job_id, failure_reason=failure_reason, **base_kwargs
        )

    if "file_type" in error_type.lower():
        file_type = response_data.get("file_type")
        supported_types = response_data.get("supported_types", [])
        return LexaUnsupportedFileError(
            message, file_type=file_type, supported_types=supported_types, **base_kwargs
        )

    # Check message content for unsupported file errors
    if "unsupported" in message.lower():
        file_type = response_data.get("file_type")
        supported_types = response_data.get("supported_types", [])
        return LexaUnsupportedFileError(
            message, file_type=file_type, supported_types=supported_types, **base_kwargs
        )

    # Authentication errors
    if status_code == 401:
        return LexaAuthError(message, **base_kwargs)

    # Authorization errors
    if status_code == 403:
        return LexaAuthError(f"Access forbidden: {message}", **base_kwargs)

    # Rate limiting
    if status_code == 429:
        retry_after = response_data.get("retry_after")
        return LexaRateLimitError(message, retry_after=retry_after, **base_kwargs)

    # Validation errors
    if status_code == 400:
        validation_errors = response_data.get("validation_errors")
        return LexaValidationError(
            message, validation_errors=validation_errors, **base_kwargs
        )

    # Not found errors
    if status_code == 404:
        return LexaError(f"Resource not found: {message}", **base_kwargs)

    # Timeout errors
    if status_code == 408:
        timeout_duration = response_data.get("timeout_duration")
        return LexaTimeoutError(
            message, timeout_duration=timeout_duration, **base_kwargs
        )

    # Unsupported file type errors by status code
    if status_code == 415:
        file_type = response_data.get("file_type")
        supported_types = response_data.get("supported_types", [])
        return LexaUnsupportedFileError(
            message, file_type=file_type, supported_types=supported_types, **base_kwargs
        )

    # Quota exceeded by status code
    if status_code == 402:
        quota_type = response_data.get("quota_type")
        reset_time = response_data.get("reset_time")
        return LexaQuotaExceededError(
            message, quota_type=quota_type, reset_time=reset_time, **base_kwargs
        )

    # Server errors
    if status_code >= 500:
        return LexaServerError(message, **base_kwargs)

    # Default to base error
    return LexaError(message, **base_kwargs)


def get_retry_strategy(error: LexaError) -> Dict[str, Any]:
    """
    Get recommended retry strategy for an error

    Provides intelligent retry guidance that competitors lack.
    """
    if not error.retry_suggested:
        return {
            "should_retry": False,
            "reason": "Error type not suitable for retry",
            "delay": 0,
            "max_retries": 0,
        }

    strategy: Dict[str, Any] = {"should_retry": True}

    if isinstance(error, LexaRateLimitError):
        strategy.update(
            {
                "delay": error.get_retry_delay(),
                "backoff": "fixed",
                "max_retries": 3,
                "reason": "Rate limit - use fixed delay",
            }
        )
    elif isinstance(error, LexaTimeoutError):
        strategy.update(
            {
                "delay": 5,
                "backoff": "exponential",
                "max_retries": 3,
                "reason": "Timeout - use exponential backoff",
            }
        )
    elif isinstance(error, LexaServerError):
        strategy.update(
            {
                "delay": 2,
                "backoff": "exponential",
                "max_retries": 5,
                "reason": "Server error - aggressive retry",
            }
        )
    elif isinstance(error, LexaJobFailedError):
        strategy.update(
            {
                "delay": 10,
                "backoff": "linear",
                "max_retries": 2,
                "reason": "Job failure - limited retry",
            }
        )
    else:
        strategy.update(
            {
                "delay": 3,
                "backoff": "exponential",
                "max_retries": 3,
                "reason": "General error - standard retry",
            }
        )

    return strategy
