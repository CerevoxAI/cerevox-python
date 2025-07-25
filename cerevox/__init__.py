"""
Cerevox - The Data Layer
"""

# Account management clients
from .account import Account
from .async_account import AsyncAccount
from .async_hippo import AsyncHippo
from .async_lexa import AsyncLexa

# Document processing
from .document_loader import (
    Document,
    DocumentBatch,
    DocumentElement,
    DocumentImage,
    DocumentMetadata,
    DocumentTable,
    chunk_markdown,
    chunk_text,
)

# Error handling
from .exceptions import (
    LexaAuthError,
    LexaError,
    LexaJobFailedError,
    LexaRateLimitError,
    LexaTimeoutError,
)

# RAG clients
from .hippo import Hippo

# Document parsing clients
from .lexa import Lexa

# Models and types
from .models import (
    AccountInfo,
    AccountPlan,
    BucketListResponse,
    CreatedResponse,
    DeletedResponse,
    FileInfo,
    FolderListResponse,
    IngestionResult,
    JobResponse,
    JobStatus,
    MessageResponse,
    ProcessingMode,
    TokenResponse,
    UpdatedResponse,
    UsageMetrics,
    User,
    UserCreate,
    UserUpdate,
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
    "DocumentMetadata",
    "DocumentTable",
    "DocumentImage",
    "DocumentElement",
    "chunk_markdown",
    "chunk_text",
    # Models and types
    "JobStatus",
    "JobResponse",
    "IngestionResult",
    "ProcessingMode",
    "FileInfo",
    "BucketListResponse",
    "FolderListResponse",
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
    # Exceptions
    "LexaError",
    "LexaAuthError",
    "LexaRateLimitError",
    "LexaTimeoutError",
    "LexaJobFailedError",
    # Version info
    "__version__",
    "__title__",
    "__description__",
    "__author__",
    "__license__",
]
