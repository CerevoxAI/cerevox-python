"""
Cerevox - The Data Layer
"""

from .clients import Account  # Account management client
from .clients import AsyncAccount  # Account management client
from .clients import AsyncHippo  # RAG client
from .clients import AsyncLexa  # Document parsing client
from .clients import Hippo  # RAG client
from .clients import Lexa  # Document parsing client

# Core models and exceptions
from .core import (  # Account models; Lexa (Document Processing) models; Exceptions
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
__version__ = "0.1.0"
__title__ = "cerevox"
__description__ = (
    "Cerevox - The Data Layer, Lexa - parse documents with enterprise-grade reliability"
)
__author__ = "Cerevox Team"
__license__ = "MIT"

__all__ = [
    # Account management clients
    "Account",
    "AsyncAccount",
    # Document parsing clients
    "Lexa",
    "AsyncLexa",
    # RAG clients
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
