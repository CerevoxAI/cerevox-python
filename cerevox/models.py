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


# Models
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
    """Status and results of a parsing job"""

    status: JobStatus = Field(..., description="Current status of the job")
    request_id: str = Field(..., description="Job identifier", alias="requestID")
    progress: int = Field(0, description="Completion percentage (0-100)")
    message: str = Field("", description="Status message")
    processed_files: Optional[int] = Field(
        None, description="Number of files processed"
    )
    total_files: Optional[int] = Field(
        None, description="Total number of files to process"
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
