"""
Cerevox SDK's Synchronous Lexa Client for Document Processing
"""

import time
import warnings
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Union,
)

from ..core import (
    FileInput,
    FileURLInput,
    JobResponse,
    JobStatus,
    LexaError,
    LexaJobFailedError,
    LexaTimeoutError,
    ProcessingMode,
)
from ..services import Ingest
from ..utils import DocumentBatch

# Optional tqdm import for progress bars
try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class Lexa(Ingest):
    """
    Official Synchronous Python Client for Cerevox Lexa Document Processing.

    This client provides a comprehensive, async-first interface to the Lexa
    document processing and parsing API, supporting intelligent extraction
    of text, metadata, and structured content from various document formats.
    The client handles complex document processing workflows including batch
    operations, cloud storage integrations, and real-time progress tracking.

    Lexa leverages advanced AI to extract structured information from documents,
    including text content, tables, images, metadata, and document relationships.

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

    Notes
    -----
    Document processing is performed asynchronously on the server. The client
    automatically polls for completion and handles job status transitions.
    Processing times vary based on document size, complexity, and chosen
    processing mode.

    Supported document formats include PDF, DOCX, DOC, TXT, HTML, RTF, PPTX,
    XLSX, CSV, and various image formats. Processing modes offer different
    trade-offs between speed and extraction quality.

    Cloud integrations require appropriate authentication and permissions
    to be configured separately for each service (AWS S3, Box, Dropbox, etc.).

    Happy Parsing! 🔍 ✨
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        data_url: str = "https://www.data.cerevox.ai",
        auth_url: str = "https://dev.cerevox.ai/v1",
        max_poll_time: float = 600.0,
        max_retries: int = 3,
        session_kwargs: Optional[dict[str, Any]] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Lexa client for document processing operations.

        Parameters
        ----------
        api_key : str, optional
            Your Cerevox API key for authentication. If None, attempts to
            read from CEREVOX_API_KEY environment variable.
        data_url : str, default "https://www.data.cerevox.ai"
            Base URL for the Lexa document processing API. This endpoint
            handles document ingestion, processing, and result retrieval.
        auth_url : str, default "https://dev.cerevox.ai/v1"
            Authentication service URL for token validation and session
            management. Separate from data processing endpoints.
        max_poll_time : float, default 600.0
            Maximum time in seconds to wait for job completion. Large documents
            or complex processing modes may require 10-30 minutes.
        max_retries : int, default 3
            Maximum retry attempts for transient failures. Must be >= 0.
            Network timeouts and temporary server errors are automatically retried.
        session_kwargs : dict
            Additional arguments to pass to requests.Session.
        timeout : float, default 30.0
            Default timeout for HTTP requests in seconds. Upload operations
            automatically use extended timeouts based on file size.
        **kwargs : dict
            Additional arguments to pass to requests.Session.

        Raises
        ------
        LexaAuthError
            If authentication fails due to invalid API key or network issues.

        Notes
        -----
        The client uses dual URL configuration with separate endpoints for
        authentication and data processing to optimize performance and security.

        Progress tracking requires the optional tqdm library. Install with
        'pip install tqdm' to enable progress bars for long-running operations.
        """
        # Initialize the base client with dual URL support
        # Lexa uses https://www.data.cerevox.ai for data requests
        # but https://dev.cerevox.ai/v1 for authentication
        super().__init__(
            api_key=api_key,
            data_url=data_url,
            auth_url=auth_url,
            product="lexa",
            max_retries=max_retries,
            session_kwargs=session_kwargs,
            timeout=timeout,
            **kwargs,
        )

        # Lexa-specific configuration
        self.max_poll_time = max_poll_time

        self.session.headers.update(
            {
                "User-Agent": "cerevox-python/0.1.0",
            }
        )

    # Private methods

    def _is_tqdm_available(self) -> bool:
        """
        Check if the tqdm library is available for progress bars.

        Returns
        -------
        bool
            True if tqdm is installed and available, False otherwise.

        Notes
        -----
        Progress bars are optional and require the tqdm library.
        Install with 'pip install tqdm' to enable progress tracking.
        """
        return TQDM_AVAILABLE and tqdm is not None

    def _create_progress_callback(
        self, show_progress: bool = False
    ) -> Optional[Callable[[JobResponse], None]]:
        """
        Create a progress callback function using tqdm if available.

        Parameters
        ----------
        show_progress : bool, default False
            Whether to create and return a progress callback function.

        Returns
        -------
        Callable[[JobResponse], None] or None
            Progress callback function that can be passed to processing
            methods, or None if progress tracking is disabled or unavailable.

        Warnings
        --------
        ImportWarning
            If show_progress is True but tqdm is not available.

        Notes
        -----
        The progress callback displays real-time information about:
        - Overall processing percentage
        - Files completed vs total files
        - Chunks processed vs total chunks
        - Number of failed chunks (if any)

        Progress bars automatically close when processing completes.
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
        Retrieve parsed documents from a completed processing job.

        Parameters
        ----------
        request_id : str
            The unique job identifier returned from document ingestion.
        max_poll_time : float, optional
            Maximum time to wait for completion. Uses instance default if None.
        poll_interval : float, optional
            Time between polling attempts. Uses instance default if None.
        progress_callback : Callable[[JobResponse], None], optional
            Function to call with status updates during processing.
        show_progress : bool, default False
            Whether to display a progress bar using tqdm.

        Returns
        -------
        DocumentBatch
            Collection of parsed documents with extracted content, metadata,
            and structured data elements.

        Notes
        -----
        This method handles both new and legacy response formats from the
        Lexa API for backward compatibility. It automatically waits for
        job completion and retrieves all processed document data.

        The DocumentBatch provides convenient access to parsed content
        including text, tables, images, and document metadata.
        """
        # Validate request_id before proceeding
        if not request_id or request_id.strip() == "":
            raise LexaError("Failed to get request ID from response")

        # Create progress callback if show_progress is True and no callback provided
        if show_progress and progress_callback is None:
            progress_callback = self._create_progress_callback(show_progress)

        status = self._wait_for_completion(
            request_id, timeout, poll_interval, progress_callback
        )

        # Handle the new response structure where results are in files field
        if status.files:
            # New format: files field contains CompletedFileData objects
            all_elements: list[Any] = []
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

    def _get_job_status(self, request_id: str) -> JobResponse:
        """
        Retrieve the current status and results of a processing job.

        Parameters
        ----------
        request_id : str
            The unique job identifier returned from ingestion endpoints.

        Returns
        -------
        JobResponse
            Object containing current job status, progress information,
            error details (if any), and results (when complete).

        Raises
        ------
        ValueError
            If request_id is empty or None.
        LexaAuthError
            If authentication fails or request_id is invalid.
        ConnectionError
            If unable to connect to the Lexa API servers.

        Notes
        -----
        Job status includes detailed progress information such as:
        - Overall completion percentage
        - Number of files and chunks processed
        - Error counts and details
        - Processing timestamps
        """
        if not request_id or request_id.strip() == "":
            raise ValueError("request_id cannot be empty")

        response = self._request("GET", f"/v0/job/{request_id}", is_data=True)
        return JobResponse(**response)

    def _wait_for_completion(
        self,
        request_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        progress_callback: Optional[Callable[[JobResponse], None]] = None,
    ) -> JobResponse:
        """
        Wait for a processing job to complete with polling and timeout handling.

        Parameters
        ----------
        request_id : str
            The unique job identifier to monitor for completion.
        max_poll_time : float, optional
            Maximum time to wait in seconds. Uses instance default if None.
        poll_interval : float, optional
            Time between polling attempts in seconds. Uses instance default if None.
        progress_callback : Callable[[JobResponse], None], optional
            Function to call with status updates during polling.

        Returns
        -------
        JobResponse
            Final job status object when processing completes successfully
            or reaches a terminal state.

        Raises
        ------
        LexaTimeoutError
            If the job does not complete within max_poll_time.
        LexaJobFailedError
            If the job fails due to processing errors or internal issues.

        Notes
        -----
        This method implements exponential backoff and handles all job
        status transitions automatically. Progress callbacks receive
        real-time updates throughout the polling process.

        Jobs in PARTIAL_SUCCESS state are considered complete and may
        contain results for successfully processed files even if some
        files failed.
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
        Parse local files and extract structured content using AI processing.

        Parameters
        ----------
        files : Union[List[FileInput], FileInput]
            Single file or list of files to process. Supports file paths
            (str), raw content (bytes), file-like objects, or FileInput objects.
        mode : Union[ProcessingMode, str], default ProcessingMode.DEFAULT
            Processing mode that determines extraction quality and speed.
            Options: DEFAULT (balanced), FAST (speed optimized),
            ENHANCED (quality optimized).
        max_poll_time : float, optional
            Maximum time to wait for completion. Overrides instance default.
        poll_interval : float, optional
            Time between status checks. Overrides instance default.
        progress_callback : Callable[[JobResponse], None], optional
            Custom function to receive processing status updates.
        show_progress : bool, default False
            Whether to display a progress bar using tqdm.

        Returns
        -------
        DocumentBatch
            Collection of processed documents with extracted text, tables,
            images, metadata, and structured content elements.

        Raises
        ------
        LexaError
            If file upload fails or request ID cannot be obtained.
        LexaTimeoutError
            If processing exceeds the maximum polling time.
        LexaJobFailedError
            If document processing fails due to format issues or errors.
        FileNotFoundError
            If any specified file paths do not exist.
        ValidationError
            If file formats are unsupported or files exceed size limits.

        Examples
        --------
        Process single document:

        >>> documents = client.parse("report.pdf")
        >>> doc = documents[0]
        >>> print(f"Title: {doc.metadata.title}")
        >>> print(f"Pages: {len(doc.pages)}")

        Batch processing with progress:

        >>> files = ["doc1.pdf", "doc2.docx", "data.xlsx"]
        >>> documents = client.parse(
        ...     files=files,
        ...     mode=ProcessingMode.ENHANCED,
        ...     show_progress=True
        ... )

        Process with custom timeout:

        >>> documents = client.parse(
        ...     files=["large_document.pdf"],
        ...     max_poll_time=1800.0,  # 30 minutes
        ...     poll_interval=5.0      # Check every 5 seconds
        ... )

        Custom progress handling:

        >>> def track_progress(status):
        ...     if status.total_files:
        ...         print(f"Progress: {status.completed_files}/{status.total_files} files")
        ...
        >>> documents = client.parse(
        ...     files=["doc1.pdf", "doc2.pdf"],
        ...     progress_callback=track_progress
        ... )

        Notes
        -----
        Supported file formats include PDF, DOCX, DOC, TXT, HTML, RTF,
        PPTX, XLSX, CSV, MD, and various image formats (PNG, JPG, TIFF).

        Processing modes offer different trade-offs:
        - FAST: Optimized for speed, basic text extraction
        - DEFAULT: Balanced quality and speed with table extraction
        - ENHANCED: Maximum quality with advanced layout analysis

        Large files or complex documents may require extended polling times.
        The client automatically handles multi-part uploads for large files.
        """

        result = self._upload_files(files, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from response")
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
        Parse documents from URLs with automatic download and processing.

        Parameters
        ----------
        urls : Union[List[FileURLInput], FileURLInput]
            Single URL string or list of URLs pointing to documents.
            Can also be FileURLInput objects with additional metadata.
        mode : Union[ProcessingMode, str], default ProcessingMode.DEFAULT
            Processing mode for document extraction and analysis.
        max_poll_time : float, optional
            Maximum time to wait for completion including download time.
        poll_interval : float, optional
            Time between status checks during processing.
        progress_callback : Callable[[JobResponse], None], optional
            Custom function to receive processing status updates.
        show_progress : bool, default False
            Whether to display a progress bar during processing.

        Returns
        -------
        DocumentBatch
            Collection of processed documents downloaded and extracted from URLs.

        Raises
        ------
        LexaError
            If URL ingestion fails or request ID cannot be obtained.
        NetworkError
            If URLs are not accessible or download fails.
        ValidationError
            If URLs point to unsupported content types.
        LexaTimeoutError
            If processing exceeds the maximum polling time.
        LexaJobFailedError
            If document processing fails after successful download.

        Examples
        --------
        Process documents from public URLs:

        >>> urls = [
        ...     "https://example.com/report.pdf",
        ...     "https://docs.example.com/manual.docx"
        ... ]
        >>> documents = client.parse_urls(urls)

        Process with custom filenames:

        >>> from ..core.models import FileURLInput
        >>> urls = [
        ...     FileURLInput(url="https://example.com/doc.pdf", filename="quarterly_report.pdf"),
        ...     FileURLInput(url="https://example.com/data.xlsx", filename="sales_data.xlsx")
        ... ]
        >>> documents = client.parse_urls(urls, mode=ProcessingMode.ENHANCED)

        Process research papers from repository:

        >>> arxiv_urls = [
        ...     "https://arxiv.org/pdf/2301.00001.pdf",
        ...     "https://arxiv.org/pdf/2301.00002.pdf"
        ... ]
        >>> documents = client.parse_urls(
        ...     urls=arxiv_urls,
        ...     show_progress=True,
        ...     max_poll_time=900.0  # 15 minutes for large papers
        ... )

        Notes
        -----
        URLs must point to publicly accessible documents without authentication
        requirements. The service automatically detects content types and
        handles various document formats.

        Download and processing times are included in the total polling timeout.
        Large documents or slow network connections may require extended timeouts.

        Custom filenames in FileURLInput objects help with organization and
        identification of processed documents in the results.
        """
        result = self._upload_urls(urls, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from response")
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

    # Cloud integration parsing methods (public)

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
        Parse all documents from an Amazon S3 folder with batch processing.

        Parameters
        ----------
        bucket_name : str
            Name of the S3 bucket containing the documents.
        folder_path : str
            Path to the folder within the bucket. Should end with '/'
            for folder processing. Supports nested folder structures.
        mode : Union[ProcessingMode, str], default ProcessingMode.DEFAULT
            Processing mode for document extraction.
        max_poll_time : float, optional
            Maximum time to wait for completion of all documents.
        poll_interval : float, optional
            Time between status checks during processing.
        progress_callback : Callable[[JobResponse], None], optional
            Custom function to receive processing status updates.
        show_progress : bool, default False
            Whether to display a progress bar during processing.

        Returns
        -------
        DocumentBatch
            Collection of all processed documents from the S3 folder.

        Raises
        ------
        LexaError
            If S3 folder access fails or request ID cannot be obtained.
        PermissionError
            If AWS credentials lack access to the specified bucket/folder.
        NotFoundError
            If the bucket or folder path does not exist.
        LexaTimeoutError
            If processing exceeds the maximum polling time.

        Examples
        --------
        Process entire folder:

        >>> documents = client.parse_s3_folder(
        ...     bucket_name="company-documents",
        ...     folder_path="reports/2024/",
        ...     mode=ProcessingMode.ENHANCED
        ... )

        Process with progress tracking:

        >>> documents = client.parse_s3_folder(
        ...     bucket_name="research-data",
        ...     folder_path="papers/ai/",
        ...     show_progress=True,
        ...     max_poll_time=3600.0  # 1 hour for large folders
        ... )

        Notes
        -----
        All supported document formats in the folder will be processed.
        Large folders may require extended polling timeouts depending on
        the number and size of documents.

        Processing is performed in batches for optimal performance and
        resource utilization.
        """
        result = self._upload_s3_folder(bucket_name, folder_path, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from response")
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

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
        Parse all documents from a Box folder with enterprise integration.

        Parameters
        ----------
        box_folder_id : str
            Unique Box folder identifier. Can be obtained from Box web interface
            or API. Use "0" for root folder access.
        mode : Union[ProcessingMode, str], default ProcessingMode.DEFAULT
            Processing mode for document extraction and analysis.
        max_poll_time : float, optional
            Maximum time to wait for completion of all documents.
        poll_interval : float, optional
            Time between status checks during processing.
        progress_callback : Callable[[JobResponse], None], optional
            Custom function to receive processing status updates.
        show_progress : bool, default False
            Whether to display a progress bar during processing.

        Returns
        -------
        DocumentBatch
            Collection of all processed documents from the Box folder.

        Raises
        ------
        LexaError
            If Box folder access fails or request ID cannot be obtained.
        PermissionError
            If Box authentication lacks access to the specified folder.
        NotFoundError
            If the folder ID does not exist or is not accessible.
        LexaTimeoutError
            If processing exceeds the maximum polling time.

        Examples
        --------
        Process Box folder:

        >>> documents = client.parse_box_folder(
        ...     box_folder_id="123456789",
        ...     mode=ProcessingMode.FAST
        ... )

        Process with detailed progress:

        >>> def detailed_progress(status):
        ...     print(f"Box Processing: {status.progress}%")
        ...     if status.total_files:
        ...         print(f"Files: {status.completed_files}/{status.total_files}")
        ...
        >>> documents = client.parse_box_folder(
        ...     box_folder_id="987654321",
        ...     progress_callback=detailed_progress
        ... )

        Notes
        -----
        Requires Box application authentication to be configured with
        appropriate OAuth2 credentials and folder access permissions.

        Box folder IDs can be found in the Box web interface URL or
        obtained via the Box API. Root folder access uses ID "0".

        The integration respects Box permissions and will only process
        files that the authenticated user can access.
        """
        result = self._upload_box_folder(box_folder_id, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from response")
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

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
        Parse all documents from a Dropbox folder with cloud integration.

        Parameters
        ----------
        folder_path : str
            Path to the Dropbox folder, starting with '/'. For example:
            '/Documents/Reports' or '/' for root folder.
        mode : Union[ProcessingMode, str], default ProcessingMode.DEFAULT
            Processing mode for document extraction and analysis.
        max_poll_time : float, optional
            Maximum time to wait for completion of all documents.
        poll_interval : float, optional
            Time between status checks during processing.
        progress_callback : Callable[[JobResponse], None], optional
            Custom function to receive processing status updates.
        show_progress : bool, default False
            Whether to display a progress bar during processing.

        Returns
        -------
        DocumentBatch
            Collection of all processed documents from the Dropbox folder.

        Raises
        ------
        LexaError
            If Dropbox folder access fails or request ID cannot be obtained.
        PermissionError
            If Dropbox authentication lacks access to the specified folder.
        NotFoundError
            If the folder path does not exist.
        LexaTimeoutError
            If processing exceeds the maximum polling time.

        Examples
        --------
        Process Dropbox folder:

        >>> documents = client.parse_dropbox_folder(
        ...     folder_path="/Work/Reports",
        ...     mode=ProcessingMode.ENHANCED
        ... )

        Process root folder with progress:

        >>> documents = client.parse_dropbox_folder(
        ...     folder_path="/",
        ...     show_progress=True,
        ...     max_poll_time=2400.0  # 40 minutes for large collections
        ... )

        Notes
        -----
        Requires Dropbox application authentication to be configured with
        appropriate OAuth2 access tokens and folder permissions.

        Folder paths must start with '/' and follow standard Dropbox
        path conventions. The integration processes all supported file
        types within the specified folder and subfolders.

        Large Dropbox folders may require extended processing times
        depending on the number of files and total data size.
        """
        result = self._upload_dropbox_folder(folder_path, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from response")
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

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
        Parse all documents from a Microsoft SharePoint folder.

        Parameters
        ----------
        drive_id : str
            Microsoft Graph Drive ID for the SharePoint site.
            Can be obtained from SharePoint admin or Graph API.
        folder_id : str
            Unique folder identifier within the SharePoint drive.
            Use "root" for the root folder of the drive.
        mode : Union[ProcessingMode, str], default ProcessingMode.DEFAULT
            Processing mode for document extraction and analysis.
        max_poll_time : float, optional
            Maximum time to wait for completion of all documents.
        poll_interval : float, optional
            Time between status checks during processing.
        progress_callback : Callable[[JobResponse], None], optional
            Custom function to receive processing status updates.
        show_progress : bool, default False
            Whether to display a progress bar during processing.

        Returns
        -------
        DocumentBatch
            Collection of all processed documents from the SharePoint folder.

        Raises
        ------
        LexaError
            If SharePoint folder access fails or request ID cannot be obtained.
        PermissionError
            If Microsoft Graph authentication lacks access to the folder.
        NotFoundError
            If the drive_id or folder_id does not exist.
        LexaTimeoutError
            If processing exceeds the maximum polling time.

        Examples
        --------
        Process SharePoint document library:

        >>> documents = client.parse_sharepoint_folder(
        ...     drive_id="b!xyz123abc...",
        ...     folder_id="root",
        ...     mode=ProcessingMode.DEFAULT
        ... )

        Process specific folder with tracking:

        >>> documents = client.parse_sharepoint_folder(
        ...     drive_id="b!xyz123abc...",
        ...     folder_id="01ABCDEF123456789",
        ...     show_progress=True
        ... )

        Notes
        -----
        Requires Microsoft Graph authentication with appropriate permissions
        for SharePoint document access. The application must be registered
        in Azure AD with necessary Graph API permissions.

        Drive IDs and folder IDs can be obtained through the Microsoft Graph
        API or SharePoint admin interfaces. Use "root" as folder_id to
        process the entire document library.

        The integration respects SharePoint permissions and processes only
        documents accessible to the authenticated user.
        """
        result = self._upload_sharepoint_folder(drive_id, folder_id, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from response")
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

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
        Parse documents from Salesforce CRM with enterprise integration.

        Parameters
        ----------
        folder_name : str
            Name of the Salesforce folder or document category to process.
            This is used for organization and identification purposes.
        mode : Union[ProcessingMode, str], default ProcessingMode.DEFAULT
            Processing mode for document extraction and analysis.
        max_poll_time : float, optional
            Maximum time to wait for completion of all documents.
        poll_interval : float, optional
            Time between status checks during processing.
        progress_callback : Callable[[JobResponse], None], optional
            Custom function to receive processing status updates.
        show_progress : bool, default False
            Whether to display a progress bar during processing.

        Returns
        -------
        DocumentBatch
            Collection of all processed documents from Salesforce.

        Raises
        ------
        LexaError
            If Salesforce integration fails or request ID cannot be obtained.
        PermissionError
            If Salesforce authentication lacks access to documents.
        LexaTimeoutError
            If processing exceeds the maximum polling time.

        Examples
        --------
        Process Salesforce documents:

        >>> documents = client.parse_salesforce_folder(
        ...     folder_name="Customer_Contracts",
        ...     mode=ProcessingMode.ENHANCED
        ... )

        Process with progress monitoring:

        >>> documents = client.parse_salesforce_folder(
        ...     folder_name="Sales_Reports",
        ...     show_progress=True,
        ...     max_poll_time=1800.0  # 30 minutes
        ... )

        Notes
        -----
        Requires Salesforce Connected App configuration with OAuth2
        authentication and appropriate document access permissions.

        The folder_name parameter is used for organization and may not
        directly correspond to Salesforce folder structures. Consult
        Salesforce integration documentation for specific setup requirements.

        Processing includes documents attached to Salesforce records,
        files in Content Libraries, and other accessible document types.
        """
        result = self._upload_salesforce_folder(folder_name, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from response")
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )

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
        Parse documents from Sendme secure file transfer service.

        Parameters
        ----------
        ticket : str
            Unique Sendme ticket identifier for accessing the file collection.
            Tickets are provided by the file sender and grant temporary access.
        mode : Union[ProcessingMode, str], default ProcessingMode.DEFAULT
            Processing mode for document extraction and analysis.
        max_poll_time : float, optional
            Maximum time to wait for completion of all documents.
        poll_interval : float, optional
            Time between status checks during processing.
        progress_callback : Callable[[JobResponse], None], optional
            Custom function to receive processing status updates.
        show_progress : bool, default False
            Whether to display a progress bar during processing.

        Returns
        -------
        DocumentBatch
            Collection of all processed documents from the Sendme ticket.

        Raises
        ------
        LexaError
            If Sendme ticket access fails or request ID cannot be obtained.
        PermissionError
            If the ticket is invalid, expired, or lacks access permissions.
        NotFoundError
            If the ticket does not exist or has been revoked.
        LexaTimeoutError
            If processing exceeds the maximum polling time.

        Examples
        --------
        Process Sendme files:

        >>> documents = client.parse_sendme_files(
        ...     ticket="abc123xyz789",
        ...     mode=ProcessingMode.FAST
        ... )

        Process with detailed tracking:

        >>> def sendme_progress(status):
        ...     print(f"Sendme Processing: {status.progress}%")
        ...     if status.error:
        ...         print(f"Error: {status.error}")
        ...
        >>> documents = client.parse_sendme_files(
        ...     ticket="def456uvw012",
        ...     progress_callback=sendme_progress
        ... )

        Notes
        -----
        Sendme tickets provide secure, time-limited access to file collections.
        Tickets may have expiration dates or download limits imposed by
        the file sender.

        The Sendme integration automatically handles secure file download
        and processes all accessible documents within the ticket scope.

        Ticket format and access methods may vary depending on the Sendme
        service configuration and sender preferences.
        """
        result = self._upload_sendme_files(ticket, mode)
        if not result.request_id:
            raise LexaError("Failed to get request ID from response")
        return self._get_documents(
            result.request_id, timeout, poll_interval, progress_callback, show_progress
        )
