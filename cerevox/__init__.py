"""
Cerevox - The Data Layer
"""

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

# Core clients
from .lexa import Lexa

# Models and types
from .models import (
    BucketListResponse,
    FileInfo,
    FolderListResponse,
    IngestionResult,
    JobResponse,
    JobStatus,
    ProcessingMode,
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
    # Core clients
    "Lexa",
    "AsyncLexa",
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
