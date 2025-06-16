"""
Cerevox SDK's Synchronous Lexa Client
"""

import json
import os
import re
import time
import warnings
from io import BytesIO
from pathlib import Path
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    List,
    Optional,
    TextIO,
    Tuple,
    Union,
)
from urllib.parse import unquote, urlparse

# Sync Request Handling
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Optional tqdm import for progress bars
try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Internal
from .document_loader import DocumentBatch
from .exceptions import (
    LexaAuthError,
    LexaError,
    LexaJobFailedError,
    LexaRateLimitError,
    LexaTimeoutError,
    LexaValidationError,
)
from .models import (
    VALID_MODES,
    BucketListResponse,
    DriveListResponse,
    FileInfo,
    FileInput,
    FileURLInput,
    FolderListResponse,
    IngestionResult,
    JobResponse,
    JobStatus,
    ProcessingMode,
    SiteListResponse,
)

HTTP = "http://"
HTTPS = "https://"
FAILED_ID = "Failed to get request ID from upload"


class Lexa:
    """
    Official Synchronous Python Client for Lexa

    This client provides a clean, Pythonic interface to the Lexa Parsing API,
    supporting file uploads, URL ingestion, and cloud storage integrations.

    Example:
        >>> client = Lexa(api_key="your-api-key")
        >>> # Parse local files
        >>> documents = client.parse("example_1.pdf")
        >>> print(documents)
        >>> documents = client.parse(["example_2.pdf", "example_2.docx"])
        >>> print(documents)
        >>> # Parse external files from URLs
        >>> documents = client.parse_urls("https://www.example.com/example_3.pdf")
        >>> print(documents)

    Happy Parsing! 🔍 ✨
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://www.data.cerevox.ai",
        max_poll_time: float = 600.0,
        max_retries: int = 3,
        session_kwargs: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Lexa client

        Args:
            api_key: Your Cerevox API key. If not provided, will try CEREVOX_API_KEY
            base_url: Base URL for the Cerevox Lexa API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            max_poll_time: Maximum time to wait for job completion in seconds
            session_kwargs: Additional arguments to pass to requests.Session
        """
        self.api_key = api_key or os.getenv("CEREVOX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it via"
                + " api_key parameter or CEREVOX_API_KEY environment variable."
            )

        # Validate base_url format
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string")

        # Basic URL validation
        if not (base_url.startswith(HTTP) or base_url.startswith(HTTPS)):
            raise ValueError(f"base_url must start with {HTTP} or {HTTPS}")

        self.base_url = base_url.rstrip("/")  # Remove trailing slash
        self.timeout = timeout
        self.max_poll_time = max_poll_time
        self.max_retries = max_retries

        # Initialize session
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[500, 501, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=0.1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount(HTTP, adapter)
        self.session.mount(HTTPS, adapter)

        # Set default headers
        self.session.headers.update(
            {
                "cerevox-api-key": self.api_key,
                "User-Agent": "cerevox-python/0.1.0",
            }
        )

        # Apply session configuration
        if session_kwargs:
            for key, value in session_kwargs.items():
                setattr(self.session, key, value)

        # Apply any additional session configuration for backward compatibility
        for key, value in kwargs.items():
            setattr(self.session, key, value)

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        All requests to Lexa API are handled by this method

        Args:
            method: The HTTP method to use
            endpoint: The API endpoint to call
            json_data: JSON data to send in the request body
            files: Files to send in the request
            params: Query parameters to send in the request
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the API

        Raises:
            LexaAuthError: If the API key is invalid
            LexaError: If the request fails
            LexaRateLimitError: If the request rate limit is exceeded
            LexaTimeoutError: If the request times out
            LexaValidationError: If the request validation fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                files=files,
                params=params,
                timeout=self.timeout,
                **kwargs,
            )

            # Handle authentication errors
            if response.status_code == 401:
                auth_error_data = response.json() if response.content else {}
                raise LexaAuthError(
                    "Invalid API key or authentication failed",
                    status_code=401,
                    response=auth_error_data,
                )

            # Handle rate limit errors
            if response.status_code == 429:
                rate_limit_error_data = response.json() if response.content else {}
                raise LexaRateLimitError(
                    rate_limit_error_data.get("error", "Rate limit exceeded"),
                    status_code=429,
                    response=rate_limit_error_data,
                )

            # Handle validation errors
            if response.status_code == 400:
                validation_error_data = response.json() if response.content else {}
                raise LexaValidationError(
                    validation_error_data.get("error", "Request validation failed"),
                    status_code=400,
                    response=validation_error_data,
                )

            # Handle other API errors
            if response.status_code >= 400:
                general_error_data: Dict[str, Any] = {}
                content_type = response.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    general_error_data = response.json()
                raise LexaError(
                    general_error_data.get(
                        "error",
                        f"API request failed with status {response.status_code}",
                    ),
                    status_code=response.status_code,
                    response=general_error_data,
                )

            try:
                response_data: Dict[str, Any] = response.json()
                return response_data
            except json.JSONDecodeError:
                # For tests that expect this to be handled gracefully
                return {}

        except requests.exceptions.Timeout as e:
            raise LexaTimeoutError(f"Request timed out: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            raise LexaError(f"Connection failed: {str(e)}")
        except requests.exceptions.RetryError as e:
            # Handle retry exhaustion - try to extract original server error
            if hasattr(e, "response") and e.response and hasattr(e.response, "json"):
                try:
                    retry_error_data = e.response.json()
                    raise LexaError(
                        retry_error_data.get(
                            "error", f"Request failed after retries: {str(e)}"
                        ),
                        status_code=getattr(e.response, "status_code", None),
                        response=retry_error_data,
                    )
                except (ValueError, AttributeError):
                    pass

            # Check if this is a 500 error that was retried
            error_str = str(e)
            if "500 error responses" in error_str:
                raise LexaError("Internal server error")

            raise LexaError(f"Request failed after retries: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise LexaError(f"Request failed: {str(e)}")

    # Private methods

    def _is_tqdm_available(self) -> bool:
        """Check if tqdm is available"""
        return TQDM_AVAILABLE and tqdm is not None

    def _create_progress_callback(
        self, show_progress: bool = False
    ) -> Optional[Callable[[JobResponse], None]]:
        """
        Create a progress callback function using tqdm if requested and available.

        Args:
            show_progress: Whether to show progress bar

        Returns:
            Progress callback function or None
        """
        if not show_progress:
            return None

        if not self._is_tqdm_available():
            warnings.warn(
                "tqdm is not available. Progress bar disabled. Install with: pip install tqdm",
                ImportWarning,
            )
            return None

        pbar = None

        def progress_callback(status: JobResponse) -> None:
            nonlocal pbar

            # Initialize progress bar on first call
            if pbar is None:
                total = 100  # Progress is in percentage
                pbar = tqdm(
                    total=total,
                    desc="Processing",
                    unit="%",
                    bar_format="{l_bar}{bar}| {n:.0f}/{total:.0f}% [{elapsed}<{remaining}, {rate_fmt}]",
                )

            # Update progress bar
            if status.progress is not None:
                # Update to current progress
                pbar.n = status.progress

                # Update description with file/chunk info
                desc_parts = ["Processing"]

                if (
                    status.total_files is not None
                    and status.completed_files is not None
                ):
                    desc_parts.append(
                        f"Files: {status.completed_files}/{status.total_files}"
                    )

                if (
                    status.total_chunks is not None
                    and status.completed_chunks is not None
                ):
                    desc_parts.append(
                        f"Chunks: {status.completed_chunks}/{status.total_chunks}"
                    )

                if status.failed_chunks and status.failed_chunks > 0:
                    desc_parts.append(f"Errors: {status.failed_chunks}")

                pbar.set_description(" | ".join(desc_parts))
                pbar.refresh()

                # Close progress bar when complete
                if status.status in [
                    JobStatus.COMPLETE,
                    JobStatus.PARTIAL_SUCCESS,
                    JobStatus.FAILED,
                ]:
                    pbar.close()

        return progress_callback

    def _get_documents(
        self,
        request_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Get parsed documents from a completed job

        Args:
            request_id: The job identifier
            timeout: Maximum time to wait in seconds (None for no timeout)
            poll_interval: Time between polling attempts in seconds
            progress_callback: Optional function to call with status updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing the parsed documents
        """
        # Create progress callback if show_progress is True and no callback provided
        if show_progress and progress_callback is None:
            progress_callback = self._create_progress_callback(show_progress)

        status = self._wait_for_completion(
            request_id, timeout, poll_interval, progress_callback
        )

        # Handle the new response structure where results are in files field
        if status.files:
            # New format: files field contains CompletedFileData objects
            all_elements: List[Any] = []
            for filename, file_data in status.files.items():
                # Check if this is CompletedFileData (has 'data' field)
                if hasattr(file_data, "data") and file_data.data:
                    # Add all elements from this file
                    all_elements.extend(file_data.data)
                elif isinstance(file_data, dict) and "data" in file_data:
                    # Handle dict representation of CompletedFileData
                    all_elements.extend(file_data["data"])

            # If we have elements, create DocumentBatch from them
            if all_elements:
                # Convert to the format expected by DocumentBatch.from_api_response
                # The DocumentBatch expects either a list of elements or a dict with 'data' field
                return DocumentBatch.from_api_response(all_elements)

        # Fallback to old format for backward compatibility
        if status.result:
            return DocumentBatch.from_api_response(status.result)

        # Return empty document batch if no data
        return DocumentBatch([])

    def _get_file_info_from_url(self, url: str) -> FileInfo:
        """
        Extract file information from a URL using HEAD request

        Args:
            url: The URL to analyze

        Returns:
            FileInfo object with name, url, and type fields
        """
        try:
            # Make HEAD request to get headers without downloading content
            response = self.session.head(url, timeout=10, allow_redirects=True)
            response.raise_for_status()

            # Extract filename from Content-Disposition header
            filename = None
            content_disposition = response.headers.get("Content-Disposition", "")
            if content_disposition:
                # Look for filename= or filename*= patterns
                filename_match = re.search(
                    r'filename\*?=["\']?([^"\';\r\n]+)', content_disposition
                )
                if filename_match:
                    filename = filename_match.group(1).strip()

            # Fallback to extracting filename from URL path
            if not filename:
                parsed_url = urlparse(url)
                filename = unquote(parsed_url.path.split("/")[-1])
                # Remove query parameters if they got included
                if "?" in filename:
                    filename = filename.split("?")[0]

            # Final fallback if no filename found
            if not filename or filename == "":
                filename = f"file_{hash(url) % 10000}"

            # Get content type from headers
            content_type = response.headers.get(
                "Content-Type", "application/octet-stream"
            )
            # Remove charset and other parameters from content type
            content_type = content_type.split(";")[0].strip()

        except Exception:
            # If HEAD request fails, use URL-based fallbacks
            try:
                parsed_url = urlparse(url)
                filename = unquote(parsed_url.path.split("/")[-1])
                if "?" in filename:
                    filename = filename.split("?")[0]
                if not filename or filename == "":
                    filename = f"file_{hash(url) % 10000}"
            except Exception:
                filename = f"file_{hash(url) % 10000}"

            content_type = "application/octet-stream"

        return FileInfo(name=filename, url=url, type=content_type)

    def _get_job_status(self, request_id: str) -> JobResponse:
        """
        Get the status and results of a parsing job

        Args:
            request_id: The job identifier returned from ingestion endpoints

        Returns:
            JobResponse object containing the current status and any results

        Raises:
            TypeError: If request_id is not a string

        """
        if not request_id or request_id.strip() == "":
            raise ValueError("request_id cannot be empty")

        response = self._request("GET", f"/v0/job/{request_id}")
        return JobResponse(**response)

    def _wait_for_completion(
        self,
        request_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
    ) -> JobResponse:
        """
        Wait for a job to complete

        Args:
            request_id: The job identifier to wait for
            timeout: Maximum time to wait in seconds (None for no timeout)
            poll_interval: Time between polling attempts in seconds
            progress_callback: Optional function to call with status updates

        Returns:
            JobResponse object when job completes

        Raises:
            LexaTimeoutError: If timeout is reached
            LexaJobFailedError: If job fails
        """
        start_time = time.time()
        poll_count = 0

        if timeout is None:
            timeout = self.max_poll_time

        while True:
            poll_count += 1
            current_time = time.time()
            elapsed_time = current_time - start_time

            status = self._get_job_status(request_id)

            if progress_callback:
                progress_callback(status)

            if status.status in [JobStatus.COMPLETE, JobStatus.PARTIAL_SUCCESS]:

                return status
            elif status.status in [
                JobStatus.FAILED,
                JobStatus.INTERNAL_ERROR,
                JobStatus.NOT_FOUND,
            ]:
                error_msg = status.error or "Job failed"

                raise LexaJobFailedError(error_msg, response={"status": status.status})

            if time.time() - start_time >= timeout:

                raise LexaTimeoutError(
                    f"Job {request_id} exceeded maximum"
                    + f" wait time of {timeout} seconds"
                )

            time.sleep(poll_interval)

    # File Ingestion

    def _upload_files(
        self,
        files: Union[List[FileInput], FileInput],
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
    ) -> IngestionResult:
        """
        Upload files for parsing

        Args:
            files: List of files to upload (supports paths, raw content, or streams)
            mode: Processing mode for the files

        Returns:
            IngestionResult containing request_id and status

        Raises:
            ValueError: If no files provided or files don't exist
            LexaError: If upload fails
        """
        # Check we have at least one file
        if not files:
            raise ValueError("At least one file must be provided")

        # If we have a single file, wrap it in a list
        if not isinstance(files, list):
            files = [files]

        # Validate mode parameter
        mode = self._validate_mode(mode)

        # Prepare files for upload
        file_objects: List[Tuple[str, Tuple[str, Union[BinaryIO, TextIO, BytesIO]]]] = (
            []
        )
        # Track files we opened so we can close them
        opened_files = []

        try:
            for i, file_input in enumerate(files):
                if isinstance(file_input, (str, Path)):
                    # Handle file paths
                    path = Path(file_input)
                    if not path.exists():
                        raise ValueError(f"File not found: {file_input}")
                    if not path.is_file():
                        raise ValueError(f"Not a file: {file_input}")

                    file_handle = open(path, "rb")
                    opened_files.append(file_handle)
                    file_objects.append(("files", (path.name, file_handle)))

                elif isinstance(file_input, (bytes, bytearray)):
                    # Handle raw content
                    content_stream = BytesIO(file_input)
                    filename = f"file_{i}.bin"  # Generate a default filename
                    file_objects.append(("files", (filename, content_stream)))

                elif hasattr(file_input, "read"):
                    # Handle file-like objects (streams)
                    filename = getattr(file_input, "name", f"stream_{i}.bin")
                    # Extract just the filename if it's a full path
                    if isinstance(filename, (str, Path)):
                        try:
                            filename = Path(filename).name
                        except (OSError, ValueError):
                            # Handle invalid path strings - keep original filename or set default
                            filename = str(filename) if filename else f"stream_{i}.bin"
                    file_objects.append(("files", (filename, file_input)))

                else:
                    raise ValueError(f"Unsupported file input type: {type(file_input)}")

            # Prepare form data
            data = {"mode": mode, "product": "lexa"}

            response = self._request(
                "POST", "/v0/files", files=dict(file_objects), params=data
            )
            return IngestionResult(**response)

        finally:
            # Close any files we opened
            for file_handle in opened_files:
                if hasattr(file_handle, "close"):
                    file_handle.close()

    def _upload_urls(
        self,
        urls: Union[List[FileURLInput], FileURLInput],
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
    ) -> IngestionResult:
        """
        Upload files from URLs

        Args:
            urls: List of URL strings
            mode: Processing mode

        Returns:
            IngestionResult with job details
        """
        # Check we have at least one file url
        if not urls:
            raise ValueError("At least one file url must be provided")

        # If we have a single file, wrap it in a list
        if not isinstance(urls, list):
            urls = [urls]

        # Validate mode parameter
        mode = self._validate_mode(mode)

        # Convert URLs to FileInfo objects using HEAD requests
        processed_urls = []
        for url in urls:
            # Validate URL format
            if not (url.startswith(HTTP) or url.startswith(HTTPS)):
                raise ValueError(f"Invalid URL format: {url}")

            # Get file info from URL
            file_info = self._get_file_info_from_url(url)
            processed_urls.append(file_info.model_dump())

        payload = {"files": processed_urls, "mode": mode, "product": "lexa"}

        data = self._request("POST", "/v0/file-urls", json_data=payload)
        return IngestionResult(**data)

    # Mode Validation
    def _validate_mode(self, mode: Union[ProcessingMode, str]) -> str:
        """
        Validate and normalize processing mode

        Args:
            mode: Processing mode to validate

        Returns:
            Normalized mode string

        Raises:
            ValueError: If mode is invalid
            TypeError: If mode is wrong type
        """
        if isinstance(mode, ProcessingMode):
            return mode.value
        elif isinstance(mode, str):
            if mode not in VALID_MODES:
                raise ValueError(
                    f"Invalid processing mode: {mode}. Valid modes are: {VALID_MODES}"
                )
            return mode
        else:
            raise TypeError(
                f"Mode must be ProcessingMode enum or string, got {type(mode)}"
            )

    # Amazon S3 Integration (private)

    def _upload_s3_folder(
        self,
        bucket_name: str,
        folder_path: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
    ) -> IngestionResult:
        """
        Upload files from an Amazon S3 folder

        Args:
            bucket_name: S3 bucket name
            folder_path: Path to the folder within the bucket
            mode: Processing mode

        Returns:
            IngestionResult with job details
        """
        # Validate mode parameter
        mode = self._validate_mode(mode)

        payload = {
            "bucket": bucket_name,
            "path": folder_path,
            "mode": mode,
            "product": "lexa",
        }

        data = self._request("POST", "/v0/amazon-folder", json_data=payload)
        return IngestionResult(**data)

    # Box Integration (private)

    def _upload_box_folder(
        self,
        box_folder_id: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
    ) -> IngestionResult:
        """
        Upload files from a Box folder

        Args:
            box_folder_id: Box folder ID to process
            mode: Processing mode

        Returns:
            IngestionResult with job details
        """
        # Validate mode parameter
        mode = self._validate_mode(mode)

        payload = {"folder_id": box_folder_id, "mode": mode, "product": "lexa"}

        data = self._request("POST", "/v0/box-folder", json_data=payload)
        return IngestionResult(**data)

    # Dropbox Integration (private)

    def _upload_dropbox_folder(
        self,
        folder_path: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
    ) -> IngestionResult:
        """
        Upload files from a Dropbox folder

        Args:
            folder_path: Dropbox folder path to process
            mode: Processing mode

        Returns:
            IngestionResult with job details
        """
        # Validate mode parameter
        mode = self._validate_mode(mode)

        payload = {"path": folder_path, "mode": mode, "product": "lexa"}

        data = self._request("POST", "/v0/dropbox-folder", json_data=payload)
        return IngestionResult(**data)

    # Microsoft SharePoint Integration (private)

    def _upload_sharepoint_folder(
        self,
        drive_id: str,
        folder_id: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
    ) -> IngestionResult:
        """
        Upload files from a Microsoft SharePoint folder

        Args:
            drive_id: Drive ID within the site
            folder_id: Microsoft folder ID to process
            mode: Processing mode

        Returns:
            IngestionResult with job details
        """
        # Validate mode parameter
        mode = self._validate_mode(mode)

        payload = {
            "drive_id": drive_id,
            "folder_id": folder_id,
            "mode": mode,
            "product": "lexa",
        }

        data = self._request("POST", "/v0/microsoft-folder", json_data=payload)
        return IngestionResult(**data)

    # Salesforce Integration (private)

    def _upload_salesforce_folder(
        self,
        folder_name: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
    ) -> IngestionResult:
        """
        Upload files from a Salesforce folder

        Args:
            folder_name: Name of the folder for organization
            mode: Processing mode

        Returns:
            IngestionResult with job details
        """
        # Validate mode parameter
        mode = self._validate_mode(mode)

        payload = {"name": folder_name, "mode": mode, "product": "lexa"}

        data = self._request("POST", "/v0/salesforce-folder", json_data=payload)
        return IngestionResult(**data)

    # Sendme Integration (private)

    def _upload_sendme_files(
        self, ticket: str, mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT
    ) -> IngestionResult:
        """
        Upload files from Sendme

        Args:
            ticket: Sendme ticket ID
            mode: Processing mode

        Returns:
            IngestionResult with job details
        """
        # Validate mode parameter
        mode = self._validate_mode(mode)

        payload = {"ticket": ticket, "mode": mode, "product": "lexa"}

        data = self._request("POST", "/v0/sendme", json_data=payload)
        return IngestionResult(**data)

    # Public methods

    def parse(
        self,
        files: Union[List[FileInput], FileInput],
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files and receive documents.

        Args:
            files: List of files to parse
            mode: Processing mode
            timeout: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """

        result = self._upload_files(files, mode)
        if not result.request_id:
            raise LexaError(FAILED_ID)
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

    def parse_urls(
        self,
        urls: Union[List[FileURLInput], FileURLInput],
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse URLs

        Args:
            urls: List of URLs to parse
            mode: Processing mode
            timeout: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = self._upload_urls(urls, mode)
        if not result.request_id:
            raise LexaError(FAILED_ID)
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

    # Amazon S3 Integration (public)

    def list_s3_buckets(self) -> BucketListResponse:
        """
        List available S3 buckets

        Returns:
            BucketListResponse containing list of available buckets
        """
        data = self._request("GET", "/v0/amazon-listBuckets")
        return BucketListResponse(**data)

    def list_s3_folders(self, bucket_name: str) -> FolderListResponse:
        """
        List folders in an S3 bucket

        Args:
            bucket_name: Name of the S3 bucket

        Returns:
            FolderListResponse containing list of folders in the bucket
        """
        data = self._request(
            "GET", "/v0/amazon-listFoldersInBucket", params={"bucket": bucket_name}
        )
        return FolderListResponse(**data)

    def parse_s3_folder(
        self,
        bucket_name: str,
        folder_path: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from an S3 folder

        Args:
            bucket_name: Name of the S3 bucket
            folder_path: Path to the folder within the bucket
            mode: Processing mode
            timeout: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = self._upload_s3_folder(bucket_name, folder_path, mode)
        if not result.request_id:
            raise LexaError(FAILED_ID)
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

    # Box Integration (public)

    def list_box_folders(self) -> FolderListResponse:
        """
        List available Box folders

        Returns:
            FolderListResponse containing list of available folders
        """
        data = self._request("GET", "/v0/box-listFolders")
        return FolderListResponse(**data)

    def parse_box_folder(
        self,
        box_folder_id: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from a Box folder

        Args:
            box_folder_id: Box folder ID to process
            mode: Processing mode
            timeout: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = self._upload_box_folder(box_folder_id, mode)
        if not result.request_id:
            raise LexaError(FAILED_ID)
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

    # Dropbox Integration (public)

    def list_dropbox_folders(self) -> FolderListResponse:
        """
        List available Dropbox folders

        Returns:
            FolderListResponse containing list of available folders
        """
        data = self._request("GET", "/v0/dropbox-listFolders")
        return FolderListResponse(**data)

    def parse_dropbox_folder(
        self,
        folder_path: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from a Dropbox folder

        Args:
            folder_path: Dropbox folder path to process
            mode: Processing mode
            timeout: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = self._upload_dropbox_folder(folder_path, mode)
        if not result.request_id:
            raise LexaError(FAILED_ID)
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

    # Microsoft SharePoint Integration (public)

    def list_sharepoint_sites(self) -> SiteListResponse:
        """
        List available SharePoint sites

        Returns:
            SiteListResponse containing list of available sites
        """
        data = self._request("GET", "/v0/microsoft-listSites")
        return SiteListResponse(**data)

    def list_sharepoint_drives(self, site_id: str) -> DriveListResponse:
        """
        List drives in a SharePoint site

        Args:
            site_id: SharePoint site ID

        Returns:
            DriveListResponse containing list of drives in the site
        """
        data = self._request(
            "GET", "/v0/microsoft-listDrivesInSite", params={"site_id": site_id}
        )
        return DriveListResponse(**data)

    def list_sharepoint_folders(self, drive_id: str) -> FolderListResponse:
        """
        List folders in a drive

        Args:
            drive_id: Drive ID

        Returns:
            FolderListResponse containing list of folders in the drive
        """
        data = self._request(
            "GET", "/v0/microsoft-listFoldersInDrive", params={"drive_id": drive_id}
        )
        return FolderListResponse(**data)

    def parse_sharepoint_folder(
        self,
        drive_id: str,
        folder_id: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from a SharePoint folder

        Args:
            drive_id: Drive ID
            folder_id: Folder ID
            mode: Processing mode
            timeout: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = self._upload_sharepoint_folder(drive_id, folder_id, mode)
        if not result.request_id:
            raise LexaError(FAILED_ID)
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

    # Salesforce Integration (public)

    def list_salesforce_folders(self) -> FolderListResponse:
        """
        List available Salesforce folders

        Returns:
            FolderListResponse containing list of available folders
        """
        data = self._request("GET", "/v0/salesforce-listFolders")
        return FolderListResponse(**data)

    def parse_salesforce_folder(
        self,
        folder_name: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from a Salesforce folder

        Args:
            folder_name: Salesforce folder name to process
            mode: Processing mode
            timeout: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = self._upload_salesforce_folder(folder_name, mode)
        if not result.request_id:
            raise LexaError(FAILED_ID)
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

    # Sendme Integration (public)

    def parse_sendme_files(
        self,
        ticket: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from Sendme

        Args:
            ticket: Sendme ticket ID
            mode: Processing mode
            timeout: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = self._upload_sendme_files(ticket, mode)
        if not result.request_id:
            raise LexaError(FAILED_ID)
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )
