"""
Cerevox SDK's Asynchronous Lexa Client
"""

import asyncio
import json
import os
import re
import time
import warnings

# Async Request Handling
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
)
from urllib.parse import unquote, urlparse

import aiofiles
import aiohttp

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

FAILED_ID = "Failed to get request ID from upload"


class AsyncLexa:
    """
    Official Async Python Client for Lexa

    This client provides a clean, Pythonic interface to the Lexa Parsing API,
    supporting file uploads, URL ingestion, and cloud storage integrations.

    Example:
        >>> async with AsyncLexa(api_key="your-api-key") as client:
        ...     # Batch upload with automatic result retrieval
        ...     documents = await client.parse_files(
        ...         files=["doc1.pdf", "doc2.docx"]
        ...     )
        ...     for doc in documents:
        ...         print(f"Processed: {doc.filename}")

    Happy Parsing! 🔍 ✨
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://www.data.cerevox.ai",
        max_concurrent: int = 10,
        max_poll_time: float = 600.0,
        max_retries: int = 3,
        poll_interval: float = 2.0,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the AsyncLexa client

        Args:
            api_key: Your Cerevox API key
            base_url: Base URL of the Cerevox API
            max_concurrent: Maximum concurrent requests for batch operations
            max_poll_time: Maximum time to poll for job completion
            max_retries: Maximum number of retries for failed requests
            poll_interval: Polling interval in seconds for job status checks
            timeout: Request timeout in seconds
            **kwargs: Additional aiohttp ClientSession arguments
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
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")

        # Validate max_retries
        if not isinstance(max_retries, int):
            raise TypeError("max_retries must be an integer")
        if max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")

        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrent = max_concurrent
        self.max_poll_time = max_poll_time
        self.max_retries = max_retries
        self.poll_interval = poll_interval

        # Session configuration
        self.session_kwargs = {
            "timeout": self.timeout,
            "headers": {
                "cerevox-api-key": self.api_key,
                "User-Agent": "cerevox-python-async/0.1.0",
            },
            **kwargs,
        }

        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)

    async def __aenter__(self) -> "AsyncLexa":
        """Async context manager entry"""
        await self.start_session()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Async context manager exit"""
        await self.close_session()

    async def start_session(self) -> None:
        """Start the aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(**self.session_kwargs)

    async def close_session(self) -> None:
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

        self._executor.shutdown(wait=True)

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[aiohttp.FormData] = None,
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
        if not self.session:
            await self.start_session()

        # Final check - if session is still None after start_session, raise error
        if self.session is None:
            raise LexaError("Session not initialized")

        # Runtime validation for max_retries
        try:
            max_retries_int = int(self.max_retries)
            if max_retries_int < 0:
                raise ValueError("Negative value")
            if max_retries_int != self.max_retries:  # Catch float/decimal cases
                raise ValueError("Non-integer value")
        except (TypeError, ValueError, OverflowError):
            raise LexaError("max_retries must be a non-negative integer")

        url = f"{self.base_url}{endpoint}"

        for attempt in range(max_retries_int + 1):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=json_data,
                    data=data,
                    params=params,
                    **kwargs,
                ) as response:

                    # Handle authentication errors
                    if response.status == 401:
                        error_data = await self._safe_json(response)
                        raise LexaAuthError(
                            "Invalid API key or authentication failed",
                            status_code=401,
                            response_data=error_data,
                        )

                    # Handle rate limit errors
                    if response.status == 429:
                        error_data = await self._safe_json(response)
                        raise LexaRateLimitError(
                            error_data.get("error", "Rate limit exceeded"),
                            status_code=429,
                            response_data=error_data,
                        )

                    # Handle validation errors
                    if response.status == 400:
                        error_data = await self._safe_json(response)
                        raise LexaValidationError(
                            error_data.get("error", "Request validation failed"),
                            status_code=400,
                            response_data=error_data,
                        )

                    # Handle other API errors
                    if response.status >= 400:
                        error_data = await self._safe_json(response)
                        raise LexaError(
                            error_data.get(
                                "error",
                                f"API request failed with status {response.status}",
                            ),
                            status_code=response.status,
                            response_data=error_data,
                        )

                    return await self._safe_json(response)

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries_int:
                    raise LexaError(
                        f"Request failed after {max_retries_int + 1} attempts: {str(e)}"
                    )

                # Exponential backoff
                wait_time = min(2**attempt, 30)
                await asyncio.sleep(wait_time)
        return {}

    async def _safe_json(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Safely parse JSON response"""
        try:
            json_data: Dict[str, Any] = await response.json()
            return json_data
        except (aiohttp.ContentTypeError, json.JSONDecodeError):
            return {}

    # Private Async Methods

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

        print(f"TQDM_AVAILABLE: {TQDM_AVAILABLE}")
        print(f"self._is_tqdm_available(): {self._is_tqdm_available()}")

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

    async def _get_documents(
        self,
        request_id: str,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Get parsed documents from a completed job

        Args:
            request_id: The job identifier
            max_poll_time: Maximum time to wait in seconds
            poll_interval: Time between polling attempts in seconds
            progress_callback: Optional function to call with status updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing the parsed documents
        """
        # Create progress callback if show_progress is True and no callback provided
        if show_progress and progress_callback is None:
            progress_callback = self._create_progress_callback(show_progress)

        status = await self._wait_for_completion(
            request_id, max_poll_time, poll_interval, progress_callback
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

    async def _get_file_info_from_url(self, url: str) -> FileInfo:
        """
        Extract file information from a URL using HEAD request

        Args:
            url: The URL to analyze

        Returns:
            FileInfo object with name, url, and type fields
        """
        if not self.session:
            await self.start_session()

        # Final check - if session is still None after start_session, raise error
        if self.session is None:
            raise LexaError("Session not initialized")

        try:
            # Make async HEAD request to get headers without downloading content
            async with self.session.head(
                url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True
            ) as response:
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
                if not filename or filename == "":
                    filename = f"file_{hash(url) % 10000}"
            except Exception:
                filename = f"file_{hash(url) % 10000}"

            content_type = "application/octet-stream"

        return FileInfo(name=filename, url=url, type=content_type)

    async def _get_job_status(self, request_id: str) -> JobResponse:
        """
        Get the status and results of a parsing job

        Args:
            request_id: The job identifier returned from ingestion endpoints

        Returns:
            JobResponse object containing the current status and any results

        Raises:
            ValueError: If request_id is empty
        """
        if not request_id or request_id.strip() == "":
            raise ValueError("request_id cannot be empty")

        async with self._semaphore:
            response = await self._request("GET", f"/v0/job/{request_id}")
            return JobResponse(**response)

    async def _wait_for_completion(
        self,
        request_id: str,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
    ) -> JobResponse:
        """
        Wait for a job to complete

        Args:
            request_id: The job identifier to wait for
            poll_interval: Time between polling attempts in seconds
            max_poll_time: Maximum time to wait in seconds (None for no timeout)
            progress_callback: Optional function to call with status updates

        Returns:
            JobResponse object when job completes

        Raises:
            LexaTimeoutError: If timeout is reached
            LexaJobFailedError: If job fails
        """
        poll_interval = poll_interval or self.poll_interval
        max_poll_time = max_poll_time or self.max_poll_time

        start_time = time.time()

        while True:
            status = await self._get_job_status(request_id)

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

            # Check max_poll_time
            if time.time() - start_time >= max_poll_time:
                raise LexaTimeoutError(
                    f"Job {request_id} exceeded maximum"
                    + f" wait time of {max_poll_time} seconds"
                )

            await asyncio.sleep(poll_interval)

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

    # Batch File Processing

    async def _upload_files(
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

        # Prepare files for upload using aiohttp.FormData
        data = aiohttp.FormData()

        try:
            for i, file_input in enumerate(files):
                if isinstance(file_input, (str, Path)):
                    # Handle file paths with async file I/O
                    path = Path(file_input)
                    if not path.exists():
                        raise ValueError(f"File not found: {file_input}")
                    if not path.is_file():
                        raise ValueError(f"Not a file: {file_input}")

                    # Read file asynchronously
                    async with aiofiles.open(path, "rb") as file:
                        file_content = await file.read()

                    data.add_field("files", file_content, filename=path.name)

                elif isinstance(file_input, (bytes, bytearray)):
                    # Handle raw content
                    filename = f"file_{i}.bin"  # Generate a default filename
                    data.add_field("files", file_input, filename=filename)

                elif hasattr(file_input, "read"):
                    # Handle file-like objects (streams)
                    raw_filename = getattr(file_input, "name", f"stream_{i}.bin")

                    # Safely extract filename
                    if isinstance(raw_filename, Path):
                        filename = raw_filename.name
                    elif isinstance(raw_filename, str):
                        filename = os.path.basename(str(raw_filename))
                    else:
                        filename = f"stream_{i}.bin"

                    # Ensure we have a valid filename
                    if not filename or filename == ".":
                        filename = f"stream_{i}.bin"

                    # Read content from file-like object
                    if hasattr(file_input, "read"):
                        if hasattr(file_input, "seek"):
                            file_input.seek(0)  # Reset position for potential reuse
                        content = file_input.read()
                        data.add_field("files", content, filename=filename)
                    else:
                        data.add_field("files", file_input, filename=filename)

                else:
                    raise ValueError(f"Unsupported file input type: {type(file_input)}")

            # Prepare query parameters
            params = {"mode": mode, "product": "lexa"}

            async with self._semaphore:
                response = await self._request(
                    "POST", "/v0/files", data=data, params=params
                )
            return IngestionResult(**response)

        except Exception as e:
            # Re-raise ValueError and LexaError as-is, wrap others in LexaError
            if isinstance(
                e,
                (
                    ValueError,
                    LexaError,
                    LexaAuthError,
                    LexaValidationError,
                    LexaRateLimitError,
                    LexaTimeoutError,
                ),
            ):
                raise
            else:
                raise LexaError(f"File upload failed: {str(e)}")

    async def _upload_urls(
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
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValueError(f"Invalid URL format: {url}")

            # Get file info from URL
            file_info = await self._get_file_info_from_url(url)
            processed_urls.append(file_info.model_dump())

        payload = {"files": processed_urls, "mode": mode, "product": "lexa"}

        async with self._semaphore:
            data = await self._request("POST", "/v0/file-urls", json_data=payload)
        return IngestionResult(**data)

    # Amazon S3 Integration (private)

    async def _upload_s3_folder(
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

        async with self._semaphore:
            data = await self._request("POST", "/v0/amazon-folder", json_data=payload)
        return IngestionResult(**data)

    # Box Integration (private)

    async def _upload_box_folder(
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

        async with self._semaphore:
            data = await self._request("POST", "/v0/box-folder", json_data=payload)
        return IngestionResult(**data)

    # Dropbox Integration (private)

    async def _upload_dropbox_folder(
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

        async with self._semaphore:
            data = await self._request("POST", "/v0/dropbox-folder", json_data=payload)
        return IngestionResult(**data)

    # Microsoft SharePoint Integration (private)

    async def _upload_sharepoint_folder(
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

        async with self._semaphore:
            data = await self._request(
                "POST", "/v0/microsoft-folder", json_data=payload
            )
        return IngestionResult(**data)

    # Salesforce Integration (private)

    async def _upload_salesforce_folder(
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

        async with self._semaphore:
            data = await self._request(
                "POST", "/v0/salesforce-folder", json_data=payload
            )
        return IngestionResult(**data)

    # Sendme Integration (private)

    async def _upload_sendme_files(
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

        async with self._semaphore:
            data = await self._request("POST", "/v0/sendme", json_data=payload)
        return IngestionResult(**data)

    # Public methods

    async def parse(
        self,
        files: Union[List[FileInput], FileInput],
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files and receive documents.

        Args:
            files: List of files to parse (supports paths, raw content, or streams)
            mode: Processing mode for the files
            max_poll_time: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = await self._upload_files(files, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from upload")
        return await self._get_documents(
            result.request_id,
            max_poll_time,
            poll_interval,
            progress_callback,
            show_progress,
        )

    async def parse_urls(
        self,
        urls: Union[List[FileURLInput], FileURLInput],
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse URLs and receive documents.

        Args:
            urls: List of URLs to parse
            mode: Processing mode
            max_poll_time: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = await self._upload_urls(urls, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from upload")
        return await self._get_documents(
            result.request_id,
            max_poll_time,
            poll_interval,
            progress_callback,
            show_progress,
        )

    # Amazon S3 Integration (public)

    async def list_s3_buckets(self) -> BucketListResponse:
        """
        List available S3 buckets

        Returns:
            BucketListResponse containing list of available buckets
        """
        async with self._semaphore:
            data = await self._request("GET", "/v0/amazon-listBuckets")
        return BucketListResponse(**data)

    async def list_s3_folders(self, bucket_name: str) -> FolderListResponse:
        """
        List folders in an S3 bucket

        Args:
            bucket_name: Name of the S3 bucket

        Returns:
            FolderListResponse containing list of folders in the bucket
        """
        async with self._semaphore:
            data = await self._request(
                "GET", "/v0/amazon-listFoldersInBucket", params={"bucket": bucket_name}
            )
        return FolderListResponse(**data)

    async def parse_s3_folder(
        self,
        bucket_name: str,
        folder_path: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from an S3 folder

        Args:
            bucket_name: Name of the S3 bucket
            folder_path: Path to the folder within the bucket
            mode: Processing mode
            max_poll_time: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = await self._upload_s3_folder(bucket_name, folder_path, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from upload")
        return await self._get_documents(
            result.request_id,
            max_poll_time,
            poll_interval,
            progress_callback,
            show_progress,
        )

    # Box Integration (public)

    async def list_box_folders(self) -> FolderListResponse:
        """
        List available Box folders

        Returns:
            FolderListResponse containing list of available folders
        """
        async with self._semaphore:
            data = await self._request("GET", "/v0/box-listFolders")
        return FolderListResponse(**data)

    async def parse_box_folder(
        self,
        box_folder_id: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from a Box folder

        Args:
            box_folder_id: Box folder ID to process
            mode: Processing mode
            max_poll_time: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = await self._upload_box_folder(box_folder_id, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from upload")
        return await self._get_documents(
            result.request_id,
            max_poll_time,
            poll_interval,
            progress_callback,
            show_progress,
        )

    # Dropbox Integration (public)

    async def list_dropbox_folders(self) -> FolderListResponse:
        """
        List available Dropbox folders

        Returns:
            FolderListResponse containing list of available folders
        """
        async with self._semaphore:
            data = await self._request("GET", "/v0/dropbox-listFolders")
        return FolderListResponse(**data)

    async def parse_dropbox_folder(
        self,
        folder_path: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from a Dropbox folder

        Args:
            folder_path: Dropbox folder path to process
            mode: Processing mode
            max_poll_time: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = await self._upload_dropbox_folder(folder_path, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from upload")
        return await self._get_documents(
            result.request_id,
            max_poll_time,
            poll_interval,
            progress_callback,
            show_progress,
        )

    # Microsoft SharePoint Integration (public)

    async def list_sharepoint_sites(self) -> SiteListResponse:
        """
        List available SharePoint sites

        Returns:
            SiteListResponse containing list of available sites
        """
        async with self._semaphore:
            data = await self._request("GET", "/v0/microsoft-listSites")
        return SiteListResponse(**data)

    async def list_sharepoint_drives(self, site_id: str) -> DriveListResponse:
        """
        List drives in a SharePoint site

        Args:
            site_id: SharePoint site ID

        Returns:
            DriveListResponse containing list of drives in the site
        """
        async with self._semaphore:
            data = await self._request(
                "GET", "/v0/microsoft-listDrivesInSite", params={"site_id": site_id}
            )
        return DriveListResponse(**data)

    async def list_sharepoint_folders(self, drive_id: str) -> FolderListResponse:
        """
        List folders in a drive

        Args:
            drive_id: Drive ID

        Returns:
            FolderListResponse containing list of folders in the drive
        """
        async with self._semaphore:
            data = await self._request(
                "GET", "/v0/microsoft-listFoldersInDrive", params={"drive_id": drive_id}
            )
        return FolderListResponse(**data)

    async def parse_sharepoint_folder(
        self,
        drive_id: str,
        folder_id: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from a SharePoint folder

        Args:
            drive_id: Drive ID within the site
            folder_id: Microsoft folder ID to process
            mode: Processing mode
            max_poll_time: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = await self._upload_sharepoint_folder(drive_id, folder_id, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from upload")
        return await self._get_documents(
            result.request_id,
            max_poll_time,
            poll_interval,
            progress_callback,
            show_progress,
        )

    # Salesforce Integration (public)

    async def list_salesforce_folders(self) -> FolderListResponse:
        """
        List available Salesforce folders

        Returns:
            FolderListResponse containing list of available folders
        """
        async with self._semaphore:
            data = await self._request("GET", "/v0/salesforce-listFolders")
        return FolderListResponse(**data)

    async def parse_salesforce_folder(
        self,
        folder_name: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from a Salesforce folder

        Args:
            folder_name: Name of the folder for organization
            mode: Processing mode
            max_poll_time: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = await self._upload_salesforce_folder(folder_name, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from upload")
        return await self._get_documents(
            result.request_id,
            max_poll_time,
            poll_interval,
            progress_callback,
            show_progress,
        )

    # Sendme Integration (public)

    async def parse_sendme_files(
        self,
        ticket: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        max_poll_time: Optional[float] = None,
        poll_interval: Optional[float] = None,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
        show_progress: bool = False,
    ) -> DocumentBatch:
        """
        Parse files from Sendme

        Args:
            ticket: Sendme ticket ID
            mode: Processing mode
            max_poll_time: Maximum time to wait for completion
            poll_interval: Time between status checks
            progress_callback: Optional callback for progress updates
            show_progress: Whether to show a progress bar using tqdm

        Returns:
            DocumentBatch containing parsed documents
        """
        result = await self._upload_sendme_files(ticket, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from upload")
        return await self._get_documents(
            result.request_id,
            max_poll_time,
            poll_interval,
            progress_callback,
            show_progress,
        )
