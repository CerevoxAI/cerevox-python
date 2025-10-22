"""
Pydantic models for the Cerevox SDK
"""

from enum import Enum
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, TextIO, Union

from pydantic import BaseModel, ConfigDict, Field

from .constants import core

REQUEST_ID_DESCRIPTION = core.REQUEST_ID_DESCRIPTION

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


class ResponseType(str, Enum):
    """Enumeration of response types for ask submissions"""

    ANSWERS = "answers"
    SOURCES = "sources"


class ReasoningLevel(str, Enum):
    """Enumeration of reasoning levels for ask submissions"""

    NONE = "none"
    BASIC = "basic"
    DETAILED = "detailed"


VALID_MODES = [mode.value for mode in ProcessingMode]


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

    html: Optional[str] = Field(None, description="Content formatted as html")
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


class BasicFileInfo(BaseModel):
    """Basic file information during early processing stages"""

    name: str = Field(..., description="Name of the file")
    filepath: Optional[str] = Field(None, description="Full path to the file")
    status: str = Field(..., description="Status of this file processing")


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

    request_id: str = Field(..., description=REQUEST_ID_DESCRIPTION, alias="requestID")
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

    request_id: str = Field(..., description=REQUEST_ID_DESCRIPTION, alias="requestID")
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

    request_id: str = Field(..., description=REQUEST_ID_DESCRIPTION, alias="requestID")
    folders: List[FolderInfo] = Field(..., description="List of available folders")

    model_config = ConfigDict(populate_by_name=True)


class IngestionResult(BaseModel):
    """Result of an ingestion operation"""

    message: str = Field(..., description="Status message")
    pages: Optional[int] = Field(None, description="Total number of pages processed")
    rejects: Optional[List[str]] = Field(None, description="List of rejected files")
    request_id: Optional[str] = Field(
        None, description=REQUEST_ID_DESCRIPTION, alias="requestID"
    )
    uploads: Optional[List[str]] = Field(
        None, description="List of successfully uploaded files"
    )

    model_config = ConfigDict(populate_by_name=True)


class JobResponse(BaseModel):
    """Status and results of a parsing job with enhanced progress tracking"""

    # Core status fields
    status: JobStatus = Field(..., description="Current status of the job")
    request_id: Optional[str] = Field(
        ..., description=REQUEST_ID_DESCRIPTION, alias="requestID"
    )

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
    files: Optional[
        Dict[str, Union[BasicFileInfo, FileProcessingInfo, CompletedFileData]]
    ] = Field(None, description="Per-file processing information or completed data")

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

    request_id: str = Field(..., description=REQUEST_ID_DESCRIPTION, alias="requestID")
    sites: List[SiteInfo] = Field(..., description="List of available sites")

    model_config = ConfigDict(populate_by_name=True)


# Account Client Models
class TokenResponse(BaseModel):
    """Response from authentication endpoints"""

    access_token: str = Field(..., description="JWT access token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: str = Field(
        ..., description="Refresh token for getting new access tokens"
    )
    token_type: str = Field(..., description="Token type (typically 'Bearer')")

    model_config = ConfigDict(populate_by_name=True)


class TokenRefreshRequest(BaseModel):
    """Request for refreshing access token"""

    refresh_token: str = Field(..., description="Refresh token")

    model_config = ConfigDict(populate_by_name=True)


class AccountInfo(BaseModel):
    """Account information"""

    account_id: str = Field(..., description="Unique account identifier")
    account_name: str = Field(..., description="Account display name")

    model_config = ConfigDict(populate_by_name=True)


class AccountPlan(BaseModel):
    """Account plan and limits information"""

    plan: str = Field(..., description="Plan name")
    base: int = Field(..., description="Base limit")
    bytes: int = Field(..., description="Storage limit in bytes")
    messages: Optional[int] = Field(None, description="Message limit")
    message_rate: Optional[int] = Field(None, description="Messages per interval")
    message_interval: Optional[int] = Field(None, description="Rate limit interval")
    bytes_overage: Optional[int] = Field(None, description="Overage bytes used")
    status: str = Field(..., description="Plan status")

    model_config = ConfigDict(populate_by_name=True)


class UsageMetrics(BaseModel):
    """Account usage metrics"""

    files: Dict[str, Any] = Field(..., description="File usage statistics")
    pages: Dict[str, Any] = Field(..., description="Page usage statistics")
    advanced_pages: Dict[str, Any] = Field(..., description="Advanced processing pages")
    storage: Dict[str, Any] = Field(..., description="Storage usage statistics")

    model_config = ConfigDict(populate_by_name=True)


class UserCreate(BaseModel):
    """Request for creating a new user"""

    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")

    model_config = ConfigDict(populate_by_name=True)


class UserUpdate(BaseModel):
    """Request for updating user information"""

    name: str = Field(..., description="Updated user display name")

    model_config = ConfigDict(populate_by_name=True)


class UserDelete(BaseModel):
    """Request for deleting a user"""

    email: str = Field(..., description="Email confirmation for deletion")

    model_config = ConfigDict(populate_by_name=True)


class User(BaseModel):
    """User information"""

    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    firstname: Optional[str] = Field(None, description="User first name")
    lastname: Optional[str] = Field(None, description="User last name")
    account_id: str = Field(..., description="Associated account ID")
    isadmin: bool = Field(..., description="Admin privileges flag")
    isbanned: bool = Field(..., description="Account banned flag")
    lastlogin: Optional[str] = Field(None, description="Last login timestamp")

    model_config = ConfigDict(populate_by_name=True)


class GenericResponse(BaseModel):
    """Generic status response"""

    status: str = Field(..., description="Operation status")

    model_config = ConfigDict(populate_by_name=True)


class MessageResponse(BaseModel):
    """Response with message and status"""

    message: str = Field(..., description="Response message")
    status: str = Field(..., description="Operation status")

    model_config = ConfigDict(populate_by_name=True)


class CreatedResponse(BaseModel):
    """Response for creation operations"""

    created: bool = Field(..., description="Creation success flag")
    status: str = Field(..., description="Operation status")

    model_config = ConfigDict(populate_by_name=True)


class UpdatedResponse(BaseModel):
    """Response for update operations"""

    updated: bool = Field(..., description="Update success flag")
    status: str = Field(..., description="Operation status")

    model_config = ConfigDict(populate_by_name=True)


class DeletedResponse(BaseModel):
    """Response for deletion operations"""

    deleted: bool = Field(..., description="Deletion success flag")
    status: str = Field(..., description="Operation status")

    model_config = ConfigDict(populate_by_name=True)


# Hippo Client Models
class FolderCreate(BaseModel):
    """Request for creating a folder"""

    folder_id: str = Field(..., description="Unique folder identifier")
    folder_name: str = Field(..., description="Folder display name")

    model_config = ConfigDict(populate_by_name=True)


class FolderItem(BaseModel):
    """Folder information"""

    folder_id: str = Field(..., description="Unique folder identifier")
    folder_name: str = Field(..., description="Folder display name")
    last_modified: Optional[str] = Field(
        None, description="Last modification timestamp"
    )
    status: Optional[str] = Field(None, description="Folder status")
    currentSize: Optional[int] = Field(None, description="Current folder size in bytes")
    historicalSize: Optional[int] = Field(
        None, description="Historical folder size in bytes"
    )

    model_config = ConfigDict(populate_by_name=True)


class FolderCreatedResponse(BaseModel):
    """Response for folder creation"""

    created: bool = Field(..., description="Creation success flag")
    status: str = Field(..., description="Operation status")
    folder_id: str = Field(..., description="Created folder ID")
    folder_name: str = Field(..., description="Created folder name")

    model_config = ConfigDict(populate_by_name=True)


class FoldersListResponse(BaseModel):
    """Response containing list of folders"""

    folders: List[FolderItem] = Field(..., description="List of folders")

    model_config = ConfigDict(populate_by_name=True)


class FileItem(BaseModel):
    """File information"""

    file_id: str = Field(..., description="Unique file identifier")
    name: str = Field(..., description="File name")
    size: Optional[int] = Field(None, description="File size in bytes")
    provider: Optional[str] = Field(None, description="File provider")
    source: Optional[str] = Field(None, description="File source")
    ts: Optional[int] = Field(None, description="Timestamp")
    type: Optional[str] = Field(None, description="File MIME type")

    model_config = ConfigDict(populate_by_name=True)


class FileUploadResponse(BaseModel):
    """Response for file upload operations"""

    uploaded: bool = Field(..., description="Upload success flag")
    status: str = Field(..., description="Operation status")
    uploads: Optional[List[str]] = Field(
        None, description="List of uploaded file names"
    )

    model_config = ConfigDict(populate_by_name=True)


class FilesListResponse(BaseModel):
    """Response containing list of files"""

    files: List[FileItem] = Field(..., description="List of files")

    model_config = ConfigDict(populate_by_name=True)


class ChatCreate(BaseModel):
    """Request for creating a chat"""

    folder_id: str = Field(..., description="Folder ID to create chat for")

    model_config = ConfigDict(populate_by_name=True)


class ChatItem(BaseModel):
    """Chat information"""

    chat_id: str = Field(..., description="Unique chat identifier")
    chat_name: Optional[str] = Field(None, description="Chat display name")
    created: Optional[str] = Field(None, description="Creation timestamp")
    folder_id: Optional[str] = Field(None, description="Associated folder ID")

    model_config = ConfigDict(populate_by_name=True)


class ChatCreatedResponse(BaseModel):
    """Response for chat creation"""

    created: bool = Field(..., description="Creation success flag")
    status: str = Field(..., description="Operation status")
    chat_id: str = Field(..., description="Created chat ID")
    chat_name: Optional[str] = Field(None, description="Created chat name")

    model_config = ConfigDict(populate_by_name=True)


class ChatsListResponse(BaseModel):
    """Response containing list of chats"""

    chats: List[ChatItem] = Field(..., description="List of chats")

    model_config = ConfigDict(populate_by_name=True)


class TextBlock(BaseModel):
    """Text block data structure"""

    data: str = Field(..., description="Text content")
    index: int = Field(..., description="Block index")
    score: int = Field(..., description="Relevance score")

    model_config = ConfigDict(populate_by_name=True)


class TableInfo(BaseModel):
    """Table information structure"""

    block_rows: int = Field(..., description="Number of block rows")
    context_rows: int = Field(..., description="Number of context rows")
    headers: List[str] = Field(..., description="Table headers")
    sheet: Optional[str] = Field(None, description="Sheet name")
    total: Optional[int] = Field(None, description="Total rows")

    model_config = ConfigDict(populate_by_name=True)


class SourceData(BaseModel):
    """Source data for ask responses"""

    text: str = Field(..., description="Source text content")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(
        ..., description="Extracted metadata with arbitrary fields"
    )

    model_config = ConfigDict(populate_by_name=True)


class AskSubmitRequest(BaseModel):
    """Request for submitting an ask"""

    query: str = Field(..., description="Question/query to ask")
    response_type: ResponseType = Field(
        ResponseType.ANSWERS,
        description="Type of response: 'answers' for AI-generated answer or 'sources' for source passages only",
    )
    citation_style: Optional[str] = Field(
        None, description="Citation style for sources"
    )
    source_ids: Optional[List[str]] = Field(
        None, description="Specific file IDs to query against"
    )
    top_k: Optional[int] = Field(
        None,
        description="Number of top relevant passages to retrieve (1-100 inclusive)",
    )
    answer_options: Optional[Dict[str, str]] = Field(
        None,
        description="Multiple choice answer options (e.g., {'A': 'option1', 'B': 'option2'})",
    )
    reasoning_level: ReasoningLevel = Field(
        ReasoningLevel.NONE,
        description="Level of reasoning to include in the response: 'none', 'basic', or 'detailed'",
    )
    include_retrieval: bool = Field(
        False,
        description="Whether the answer_options should be included in the retrieval process",
    )
    mode: str = Field(
        "lite",
        description="Query processing mode: 'lite' for faster processing or 'pro' for more comprehensive analysis",
    )

    model_config = ConfigDict(populate_by_name=True)


class SimpleSourceData(BaseModel):
    """Simplified source data structure (for GET /asks/{index} responses)"""

    text: str = Field(..., description="Source text content")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(
        ..., description="Extracted metadata with arbitrary fields"
    )

    model_config = ConfigDict(populate_by_name=True)


# For POST /asks responses
class AskSubmitResponse(BaseModel):
    ask_index: int = Field(..., description="Index of the created ask")
    query: Optional[str] = Field(None, description="The question asked")
    reply: Optional[str] = Field(None, description="The response received")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the answer")
    source_data: Optional[List[SourceData]] = Field(
        None, description="Full source data"
    )

    model_config = ConfigDict(populate_by_name=True)


# For GET /asks list responses
class AskListItem(BaseModel):
    ask_index: int = Field(..., description="Index of the ask")
    ask_ts: int = Field(..., description="Ask timestamp (Unix timestamp)")
    query: Optional[str] = Field(None, description="The question asked")
    reply: Optional[str] = Field(None, description="The response received")

    model_config = ConfigDict(populate_by_name=True)


# For GET /asks/{index} responses (can optionally include simplified source_data)
class AskItem(BaseModel):
    ask_index: int = Field(..., description="Index of the ask")
    ask_ts: int = Field(..., description="Ask timestamp (Unix timestamp)")
    query: Optional[str] = Field(None, description="The question asked")
    reply: Optional[str] = Field(None, description="The response received")
    filenames: Optional[List[str]] = Field(
        None, description="Source filenames (if show_files=true)"
    )
    source_data: Optional[List[SimpleSourceData]] = Field(
        None, description="Simplified source data (if show_source=true)"
    )

    model_config = ConfigDict(populate_by_name=True)


class AsksListResponse(BaseModel):
    """Response containing list of asks"""

    ask_count: int = Field(..., description="Number of asks")
    asks: List[AskListItem] = Field(..., description="List of asks")

    model_config = ConfigDict(populate_by_name=True)
