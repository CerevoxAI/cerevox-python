"""
Async Data Ingestion Service for Cerevox SDK

This module provides asynchronous data ingestion capabilities for document processing
and RAG operations, supporting multiple file sources including local files, URLs,
and cloud storage providers.
"""

import asyncio
import json
import os
import re
import time
import warnings
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

from ..core import (
    VALID_MODES,
    BucketListResponse,
    DriveListResponse,
    FileInfo,
    FileInput,
    FileURLInput,
    FolderListResponse,
    IngestionResult,
    LexaAuthError,
    LexaError,
    LexaRateLimitError,
    LexaTimeoutError,
    LexaValidationError,
    ProcessingMode,
    SiteListResponse,
)
from ..core.async_client import AsyncClient


class AsyncIngest(AsyncClient):
    """
    Async data ingestion service for Cerevox SDK

    Provides async methods for uploading and processing documents from various sources:
    - Local files and file streams
    - URLs pointing to documents
    - Cloud storage providers (S3, Box, Dropbox, SharePoint, Salesforce)

    This service handles all async data ingestion functionality that can be shared
    between different Cerevox products (Lexa, Hippo).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        data_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        product: Optional[str] = None,
        max_concurrent: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the AsyncIngest service

        Args:
            api_key: User Personal Access Token (PAT) for authentication
            data_url: Base URL for the Cerevox API (used for data requests)
            auth_url: Base URL for authentication (defaults to data_url if not provided)
            product: Product identifier for ingestion requests (e.g., "lexa", "hippo")
            max_concurrent: Maximum number of concurrent requests (default: 10)
            **kwargs: Additional arguments passed to base client
        """
        super().__init__(api_key, data_url, auth_url, **kwargs)
        self.product = product
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

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
            params = {"mode": mode, "product": self.product}

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

        # Convert URLs to FileInfo objects using async HEAD requests
        processed_urls = []
        for url in urls:
            # Validate URL format
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValueError(f"Invalid URL format: {url}")

            # Get file info from URL
            file_info = await self._get_file_info_from_url(url)
            processed_urls.append(file_info.model_dump())

        payload = {"files": processed_urls, "mode": mode, "product": self.product}

        async with self._semaphore:
            data = await self._request("POST", "/v0/file-urls", json_data=payload)
        return IngestionResult(**data)

    # Amazon S3 Integration

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
            "product": self.product,
        }

        async with self._semaphore:
            data = await self._request("POST", "/v0/amazon-folder", json_data=payload)
        return IngestionResult(**data)

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

    # Box Integration

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

        payload = {"folder_id": box_folder_id, "mode": mode, "product": self.product}

        async with self._semaphore:
            data = await self._request("POST", "/v0/box-folder", json_data=payload)
        return IngestionResult(**data)

    async def list_box_folders(self) -> FolderListResponse:
        """
        List available Box folders

        Returns:
            FolderListResponse containing list of available folders
        """
        async with self._semaphore:
            data = await self._request("GET", "/v0/box-listFolders")
        return FolderListResponse(**data)

    # Dropbox Integration

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

        payload = {"path": folder_path, "mode": mode, "product": self.product}

        async with self._semaphore:
            data = await self._request("POST", "/v0/dropbox-folder", json_data=payload)
        return IngestionResult(**data)

    async def list_dropbox_folders(self) -> FolderListResponse:
        """
        List available Dropbox folders

        Returns:
            FolderListResponse containing list of available folders
        """
        async with self._semaphore:
            data = await self._request("GET", "/v0/dropbox-listFolders")
        return FolderListResponse(**data)

    # Microsoft SharePoint Integration

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
            "product": self.product,
        }

        async with self._semaphore:
            data = await self._request(
                "POST", "/v0/microsoft-folder", json_data=payload
            )
        return IngestionResult(**data)

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

    # Salesforce Integration

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

        payload = {"name": folder_name, "mode": mode, "product": self.product}

        async with self._semaphore:
            data = await self._request(
                "POST", "/v0/salesforce-folder", json_data=payload
            )
        return IngestionResult(**data)

    async def list_salesforce_folders(self) -> FolderListResponse:
        """
        List available Salesforce folders

        Returns:
            FolderListResponse containing list of available folders
        """
        async with self._semaphore:
            data = await self._request("GET", "/v0/salesforce-listFolders")
        return FolderListResponse(**data)

    # Sendme Integration

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

        payload = {"ticket": ticket, "mode": mode, "product": self.product}

        async with self._semaphore:
            data = await self._request("POST", "/v0/sendme", json_data=payload)
        return IngestionResult(**data)
