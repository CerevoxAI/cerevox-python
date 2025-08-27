"""
Data Ingestion Service for Cerevox SDK

This module provides data ingestion capabilities for document processing and RAG operations,
supporting multiple file sources including local files, URLs, and cloud storage providers.
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

from ..core.client import Client
from ..core.models import (
    VALID_MODES,
    BucketListResponse,
    DriveListResponse,
    FileInfo,
    FileInput,
    FileURLInput,
    FolderListResponse,
    IngestionResult,
    ProcessingMode,
    SiteListResponse,
)

HTTP = "http://"
HTTPS = "https://"


class Ingest(Client):
    """
    Data ingestion service for Cerevox SDK

    Provides methods for uploading and processing documents from various sources:
    - Local files and file streams
    - URLs pointing to documents
    - Cloud storage providers (S3, Box, Dropbox, SharePoint, Salesforce)

    This service handles all data ingestion functionality that can be shared
    between different Cerevox products (Lexa, Hippo).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://dev.cerevox.ai/v1",
        data_url: str = "https://data.cerevox.ai",
        product: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Ingest service

        Args:
            api_key: User Personal Access Token (PAT) for authentication
            base_url : str, default "https://dev.cerevox.ai/v1" Base URL for cerevox requests.
            data_url : str, default "https://data.cerevox.ai" Data URL for cerevox requests.
            product: Product identifier for ingestion requests (e.g., "lexa", "hippo")
            **kwargs: Additional arguments passed to base client
        """
        super().__init__(api_key, base_url, data_url, **kwargs)
        self.product = product

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

    def _upload_files(
        self,
        files: Union[List[FileInput], FileInput],
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        folder_id: Optional[str] = None,
    ) -> IngestionResult:
        """
        Upload files for parsing

        Args:
            files: List of files to upload (supports paths, raw content, or streams)
            mode: Processing mode
            folder_id: Optional Hippo folder ID for RAG operations for the files

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
            data = {"mode": mode, "product": self.product}
            if folder_id is not None:
                data["folder_id"] = folder_id

            response = self._request(
                "POST", "/v0/files", files=dict(file_objects), params=data, is_data=True
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
        folder_id: Optional[str] = None,
    ) -> IngestionResult:
        """
        Upload files from URLs

        Args:
            urls: List of URL strings
            mode: Processing mode
            folder_id: Optional Hippo folder ID for RAG operations

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

        payload = {"files": processed_urls, "mode": mode, "product": self.product}
        if folder_id is not None:
            payload["folder_id"] = folder_id

        data = self._request("POST", "/v0/file-urls", json_data=payload, is_data=True)
        return IngestionResult(**data)

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

    # Amazon S3 Integration

    def _upload_s3_folder(
        self,
        bucket_name: str,
        folder_path: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        folder_id: Optional[str] = None,
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
        if folder_id is not None:
            payload["folder_id"] = folder_id

        data = self._request(
            "POST", "/v0/amazon-folder", json_data=payload, is_data=True
        )
        return IngestionResult(**data)

    def list_s3_buckets(self) -> BucketListResponse:
        """
        List available S3 buckets

        Returns:
            BucketListResponse containing list of available buckets
        """
        data = self._request("GET", "/v0/amazon-listBuckets", is_data=True)
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
            "GET",
            "/v0/amazon-listFoldersInBucket",
            params={"bucket": bucket_name},
            is_data=True,
        )
        return FolderListResponse(**data)

    # Box Integration

    def _upload_box_folder(
        self,
        box_folder_id: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        folder_id: Optional[str] = None,
    ) -> IngestionResult:
        """
        Upload files from a Box folder

        Args:
            box_folder_id: Box folder ID to process
            mode: Processing mode
            folder_id: Optional Hippo folder ID for RAG operations

        Returns:
            IngestionResult with job details
        """
        # Validate mode parameter
        mode = self._validate_mode(mode)

        payload = {
            "box_folder_id": box_folder_id,
            "mode": mode,
            "product": self.product,
        }
        if folder_id is not None:
            payload["folder_id"] = folder_id

        data = self._request("POST", "/v0/box-folder", json_data=payload, is_data=True)
        return IngestionResult(**data)

    def list_box_folders(self) -> FolderListResponse:
        """
        List available Box folders

        Returns:
            FolderListResponse containing list of available folders
        """
        data = self._request("GET", "/v0/box-listFolders", is_data=True)
        return FolderListResponse(**data)

    # Dropbox Integration

    def _upload_dropbox_folder(
        self,
        folder_path: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        folder_id: Optional[str] = None,
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
        if folder_id is not None:
            payload["folder_id"] = folder_id

        data = self._request(
            "POST", "/v0/dropbox-folder", json_data=payload, is_data=True
        )
        return IngestionResult(**data)

    def list_dropbox_folders(self) -> FolderListResponse:
        """
        List available Dropbox folders

        Returns:
            FolderListResponse containing list of available folders
        """
        data = self._request("GET", "/v0/dropbox-listFolders", is_data=True)
        return FolderListResponse(**data)

    # Microsoft SharePoint Integration

    def _upload_sharepoint_folder(
        self,
        drive_id: str,
        sharepoint_folder_id: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        folder_id: Optional[str] = None,
    ) -> IngestionResult:
        """
        Upload files from a Microsoft SharePoint folder

        Args:
            drive_id: Drive ID within the site
            sharepoint_folder_id: Microsoft folder ID to process
            mode: Processing mode
            folder_id: Optional Hippo folder ID for RAG operations

        Returns:
            IngestionResult with job details
        """
        # Validate mode parameter
        mode = self._validate_mode(mode)

        payload = {
            "drive_id": drive_id,
            "sharepoint_folder_id": sharepoint_folder_id,
            "mode": mode,
            "product": self.product,
        }
        if folder_id is not None:
            payload["folder_id"] = folder_id

        data = self._request(
            "POST", "/v0/microsoft-folder", json_data=payload, is_data=True
        )
        return IngestionResult(**data)

    def list_sharepoint_sites(self) -> SiteListResponse:
        """
        List available SharePoint sites

        Returns:
            SiteListResponse containing list of available sites
        """
        data = self._request("GET", "/v0/microsoft-listSites", is_data=True)
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
            "GET",
            "/v0/microsoft-listDrivesInSite",
            params={"site_id": site_id},
            is_data=True,
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
            "GET",
            "/v0/microsoft-listFoldersInDrive",
            params={"drive_id": drive_id},
            is_data=True,
        )
        return FolderListResponse(**data)

    # Salesforce Integration

    def _upload_salesforce_folder(
        self,
        folder_name: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        folder_id: Optional[str] = None,
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
        if folder_id is not None:
            payload["folder_id"] = folder_id

        data = self._request(
            "POST", "/v0/salesforce-folder", json_data=payload, is_data=True
        )
        return IngestionResult(**data)

    def list_salesforce_folders(self) -> FolderListResponse:
        """
        List available Salesforce folders

        Returns:
            FolderListResponse containing list of available folders
        """
        data = self._request("GET", "/v0/salesforce-listFolders", is_data=True)
        return FolderListResponse(**data)

    # Sendme Integration

    def _upload_sendme_files(
        self,
        ticket: str,
        mode: Union[ProcessingMode, str] = ProcessingMode.DEFAULT,
        folder_id: Optional[str] = None,
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
        if folder_id is not None:
            payload["folder_id"] = folder_id

        data = self._request("POST", "/v0/sendme", json_data=payload, is_data=True)
        return IngestionResult(**data)
