"""
Cerevox - The Data Layer
"""

from .apis import Account  # Account Management API
from .apis import AsyncAccount  # Async Account Management API
from .apis import AsyncHippo  # Async RAG API
from .apis import AsyncLexa  # Async Document Processing API
from .apis import Hippo  # RAG API
from .apis import Lexa  # Document Processing API

# Core models and exceptions
from .core import (
    AccountInfo,
    AccountPlan,
    BucketListResponse,
    CreatedResponse,
    DeletedResponse,
    FolderListResponse,
    IngestionResult,
    JobResponse,
    JobStatus,
    LexaAuthError,
    LexaError,
    LexaJobFailedError,
    LexaRateLimitError,
    LexaTimeoutError,
    MessageResponse,
    ProcessingMode,
    TokenResponse,
    UpdatedResponse,
    UsageMetrics,
    User,
    UserCreate,
    UserUpdate,
)

# Document processing
from .utils import (
    Document,
    DocumentBatch,
    DocumentElement,
    DocumentImage,
    DocumentMetadata,
    DocumentTable,
    ElementContent,
    ElementStats,
    FileInfo,
    PageInfo,
    SourceInfo,
    chunk_markdown,
    chunk_text,
)

# Version info
__version__ = "0.2.0"
__title__ = "cerevox"
__description__ = "Cerevox - The Data Layer for AI Agents: data parsing (Lexa) and data search (Hippo)"
__author__ = "Cerevox Team"
__license__ = "MIT"

__all__ = [
    # Account Management API
    "Account",
    "AsyncAccount",
    # Document Processing API
    "Lexa",
    "AsyncLexa",
    # RAG API
    "Hippo",
    "AsyncHippo",
    # Document processing
    "Document",
    "DocumentBatch",
    "DocumentElement",
    "DocumentImage",
    "DocumentMetadata",
    "DocumentTable",
    "ElementContent",
    "ElementStats",
    "FileInfo",
    "PageInfo",
    "SourceInfo",
    "chunk_markdown",
    "chunk_text",
    # Account models
    "AccountInfo",
    "AccountPlan",
    "CreatedResponse",
    "DeletedResponse",
    "MessageResponse",
    "TokenResponse",
    "UpdatedResponse",
    "User",
    "UserCreate",
    "UserUpdate",
    "UsageMetrics",
    # Lexa (Document Processing) models
    "BucketListResponse",
    "FolderListResponse",
    "IngestionResult",
    "JobResponse",
    "JobStatus",
    "ProcessingMode",
    # Exceptions
    "LexaAuthError",
    "LexaError",
    "LexaJobFailedError",
    "LexaRateLimitError",
    "LexaTimeoutError",
    # Version info
    "__version__",
    "__title__",
    "__description__",
    "__author__",
    "__license__",
]
