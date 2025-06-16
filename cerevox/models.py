"""
Pydantic models for the Cerevox SDK
"""

from enum import Enum
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, TextIO, Union

from pydantic import BaseModel, ConfigDict, Field

# Supported file inputs
## URLs
FileURLInput = str
## Paths
FilePathInput = Union[Path, str]
## Raw Content
FileContentInput = Union[bytes, bytearray]
## File-like streams
FileStreamInput = Union[BinaryIO, TextIO, BytesIO, StringIO]
## Aggregated File Inputs
FileInput = Union[FilePathInput, FileContentInput, FileStreamInput]

REQUEST_IDENTIFIER = "Request identifier"


# Enums
class JobStatus(str, Enum):
    """Enumeration of possible job statuses"""

    COMPLETE = "complete"
    FAILED = "failed"
    INTERNAL_ERROR = "internal_error"
    NOT_FOUND = "not_found"
    PARTIAL_SUCCESS = "partial_success"
    PROCESSING = "processing"


class ProcessingMode(str, Enum):
    """Enumeration of processing modes"""

    ADVANCED = "advanced"
    DEFAULT = "default"


VALID_MODES = [mode.value for mode in ProcessingMode]


# New models for richer response structure
class ElementSourceInfo(BaseModel):
    """Information about extracted element characteristics"""

    characters: int = Field(..., description="Number of characters in the element")
    words: int = Field(..., description="Number of words in the element")
    sentences: int = Field(..., description="Number of sentences in the element")


class PageSourceInfo(BaseModel):
    """Information about the page source"""

    page_number: int = Field(..., description="Page number in the document")
    index: int = Field(..., description="Index of the element on this page")


class FileSourceInfo(BaseModel):
    """Information about the file source"""

    extension: str = Field(..., description="File extension")
    id: str = Field(..., description="File identifier")
    index: int = Field(..., description="Index of this element in the file")
    mime_type: str = Field(..., description="MIME type of the file")
    original_mime_type: str = Field(..., description="Original MIME type of the file")
    name: str = Field(..., description="Name of the file")


class SourceInfo(BaseModel):
    """Source information for extracted content"""

    file: FileSourceInfo = Field(..., description="File source information")
    page: PageSourceInfo = Field(..., description="Page source information")
    element: ElementSourceInfo = Field(..., description="Element characteristics")


class ContentInfo(BaseModel):
    """Content extracted from document"""

    html: str = Field(..., description="Content formatted as html")
    markdown: str = Field(..., description="Content formatted as markdown")
    text: str = Field(..., description="Plain text content")


class ContentElement(BaseModel):
    """Individual content element extracted from document"""

    content: ContentInfo = Field(..., description="The extracted content")
    element_type: str = Field(
        ..., description="Type of element (e.g., paragraph, table)"
    )
    id: str = Field(..., description="Unique identifier for this element")
    source: SourceInfo = Field(..., description="Source information for this element")


class FileProcessingInfo(BaseModel):
    """Processing information for an individual file"""

    name: str = Field(..., description="Name of the file")
    filepath: str = Field(..., description="Full path to the file")
    total_chunks: int = Field(..., description="Total number of chunks for this file")
    completed_chunks: int = Field(..., description="Number of completed chunks")
    failed_chunks: int = Field(..., description="Number of failed chunks")
    processing_chunks: int = Field(
        ..., description="Number of chunks currently processing"
    )
    status: str = Field(..., description="Status of this file processing")
    last_updated: int = Field(
        ..., description="Timestamp of last update (milliseconds)"
    )


class CompletedFileData(BaseModel):
    """Data structure for completed file processing"""

    data: List[ContentElement] = Field(..., description="Extracted content elements")
    errors: Dict[str, str] = Field(
        default_factory=dict, description="Processing errors by chunk/element"
    )
    error_count: int = Field(0, description="Total number of errors for this file")


# Updated models
class BucketInfo(BaseModel):
    """Information about an S3 bucket"""

    name: str = Field(..., description="Bucket name", alias="Name")
    creation_date: str = Field(
        ..., description="When the bucket was created", alias="CreationDate"
    )

    model_config = ConfigDict(populate_by_name=True)


class BucketListResponse(BaseModel):
    """Response containing list of S3 buckets"""

    request_id: str = Field(..., description=REQUEST_IDENTIFIER, alias="requestID")
    buckets: List[BucketInfo] = Field(..., description="List of available buckets")

    model_config = ConfigDict(populate_by_name=True)


class DriveInfo(BaseModel):
    """Information about a SharePoint drive"""

    id: str = Field(..., description="Drive identifier")
    name: str = Field(..., description="Drive name")
    drive_type: str = Field(..., description="Type of drive", alias="driveType")

    model_config = ConfigDict(populate_by_name=True)


class DriveListResponse(BaseModel):
    """Response containing list of SharePoint drives"""

    request_id: str = Field(..., description=REQUEST_IDENTIFIER, alias="requestID")
    drives: List[DriveInfo] = Field(..., description="List of available drives")

    model_config = ConfigDict(populate_by_name=True)


class FileInfo(BaseModel):
    """Information about a file to be processed"""

    name: str = Field(..., description="Name of the file")
    url: str = Field(..., description="URL to download the file from")
    type: str = Field(..., description="MIME type of the file")


class FolderInfo(BaseModel):
    """Information about a folder"""

    id: str = Field(..., description="Folder identifier")
    name: str = Field(..., description="Folder name")
    path: Optional[str] = Field(None, description="Full folder path")


class FolderListResponse(BaseModel):
    """Response containing list of folders"""

    request_id: str = Field(..., description=REQUEST_IDENTIFIER, alias="requestID")
    folders: List[FolderInfo] = Field(..., description="List of available folders")

    model_config = ConfigDict(populate_by_name=True)


class IngestionResult(BaseModel):
    """Result of an ingestion operation"""

    message: str = Field(..., description="Status message")
    pages: Optional[int] = Field(None, description="Total number of pages processed")
    rejects: Optional[List[str]] = Field(None, description="List of rejected files")
    request_id: str = Field(
        ..., description="Job identifier for tracking", alias="requestID"
    )
    uploads: Optional[List[str]] = Field(
        None, description="List of successfully uploaded files"
    )

    model_config = ConfigDict(populate_by_name=True)


class JobResponse(BaseModel):
    """Status and results of a parsing job with enhanced progress tracking"""

    # Core status fields
    status: JobStatus = Field(..., description="Current status of the job")
    request_id: str = Field(..., description="Job identifier", alias="requestID")

    # Processing progress fields (for processing jobs)
    age_seconds: Optional[int] = Field(None, description="Age of the job in seconds")
    progress: Optional[int] = Field(None, description="Completion percentage (0-100)")
    created_at: Optional[int] = Field(
        None, description="Job creation timestamp (milliseconds)"
    )

    # Chunk-level progress
    completed_chunks: Optional[int] = Field(
        None, description="Number of completed chunks"
    )
    failed_chunks: Optional[int] = Field(None, description="Number of failed chunks")
    processing_chunks: Optional[int] = Field(
        None, description="Number of chunks currently processing"
    )
    total_chunks: Optional[int] = Field(None, description="Total number of chunks")

    # File-level progress
    total_files: Optional[int] = Field(None, description="Total number of files")
    completed_files: Optional[int] = Field(
        None, description="Number of completed files"
    )
    failed_files: Optional[int] = Field(None, description="Number of failed files")
    processing_files: Optional[int] = Field(
        None, description="Number of files currently processing"
    )

    # Detailed file information
    files: Optional[Dict[str, Union[FileProcessingInfo, CompletedFileData]]] = Field(
        None, description="Per-file processing information or completed data"
    )

    # Error handling
    errors: Optional[Dict[str, Union[str, Dict[str, str]]]] = Field(
        None, description="Error details by file or general errors"
    )
    error_count: Optional[int] = Field(None, description="Total number of errors")

    # Legacy fields for backward compatibility
    message: Optional[str] = Field(None, description="Status message")
    processed_files: Optional[int] = Field(
        None, description="Number of files processed"
    )
    result: Optional[Dict[str, Any]] = Field(
        None, description="Parsing results (when completed)"
    )
    results: Optional[List[Dict[str, Any]]] = Field(
        None, description="Individual file results"
    )
    error: Optional[str] = Field(None, description="Error details (when failed)")

    model_config = ConfigDict(populate_by_name=True)


class SiteInfo(BaseModel):
    """Information about a SharePoint site"""

    id: str = Field(..., description="Site identifier")
    name: str = Field(..., description="Site name")
    web_url: str = Field(..., description="Site URL", alias="webUrl")

    model_config = ConfigDict(populate_by_name=True)


class SiteListResponse(BaseModel):
    """Response containing list of SharePoint sites"""

    request_id: str = Field(..., description=REQUEST_IDENTIFIER, alias="requestID")
    sites: List[SiteInfo] = Field(..., description="List of available sites")

    model_config = ConfigDict(populate_by_name=True)
