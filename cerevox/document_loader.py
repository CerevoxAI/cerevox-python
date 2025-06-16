"""
Document parsing utilities for the Cerevox SDK
"""

import importlib
import re
import uuid
import warnings
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

# Optional pandas import for advanced table features

try:
    import pandas

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    warnings.warn(
        "Pandas not available. Pandas table conversion will be disabled."
        + " Install with: pip install pandas",
        ImportWarning,
    )

# Optional BeautifulSoup import for HTML tableparsing
try:
    from bs4 import BeautifulSoup, Tag

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    warnings.warn(
        "BeautifulSoup4 not available. HTML table parsing will be disabled."
        + " Install with: pip install beautifulsoup4",
        ImportWarning,
    )

END_DIV = "</div>"
SENTENCE_REGEX = r"[.!?]+(?=\s|$|[*_`\]])"


@dataclass
class ElementContent:
    """Content of a document element in different formats"""

    html: Optional[str] = None
    markdown: Optional[str] = None
    text: Optional[str] = None


@dataclass
class ElementStats:
    """Statistics for a document element"""

    characters: int = 0
    words: int = 0
    sentences: int = 0


@dataclass
class PageInfo:
    """Information about a page in the document"""

    page_number: int
    index: int


@dataclass
class FileInfo:
    """Information about the source file"""

    extension: str
    id: str
    index: int
    mime_type: str
    original_mime_type: str
    name: str


@dataclass
class SourceInfo:
    """Source information for a document element"""

    file: FileInfo
    page: PageInfo
    element: ElementStats


@dataclass
class DocumentElement:
    """Individual element from the API response"""

    content: ElementContent
    element_type: str  # table, paragraph, image, etc.
    id: str
    source: SourceInfo

    @property
    def html(self) -> str:
        """Get HTML content"""
        return self.content.html or ""

    @property
    def markdown(self) -> str:
        """Get Markdown content"""
        return self.content.markdown or ""

    @property
    def text(self) -> str:
        """Get plain text content"""
        return self.content.text or ""

    @property
    def page_number(self) -> int:
        """Get page number"""
        return self.source.page.page_number

    @property
    def filename(self) -> str:
        """Get source filename"""
        return self.source.file.name

    @property
    def file_extension(self) -> str:
        """Get file extension"""
        return self.source.file.extension


@dataclass
class DocumentMetadata:
    """Metadata for a processed document"""

    filename: str
    file_type: Optional[str] = None
    file_id: Optional[str] = None
    mime_type: Optional[str] = None
    original_mime_type: Optional[str] = None
    total_elements: Optional[int] = None
    total_pages: Optional[int] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentTable:
    """Enhanced extracted table from a document with competitive features"""

    element_id: str
    headers: List[str]
    rows: List[List[str]]
    page_number: int
    html: Optional[str] = None
    markdown: Optional[str] = None
    table_index: Optional[int] = None
    caption: Optional[str] = None

    def to_pandas(self) -> Optional["pandas.DataFrame"]:
        """Convert table to pandas DataFrame (competitive feature)"""
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for to_pandas(). Install with: pip install pandas"
            )

        pandas = importlib.import_module("pandas")
        if not self.rows:
            return pandas.DataFrame()

        # Use headers if available, otherwise generate column names
        columns = (
            self.headers
            if self.headers
            else [f"Column_{i+1}" for i in range(len(self.rows[0]))]
        )

        return pandas.DataFrame(self.rows, columns=columns)

    def to_csv_string(self) -> str:
        """Convert table to CSV string"""
        lines = []
        if self.headers:
            lines.append(",".join(f'"{header}"' for header in self.headers))

        for row in self.rows:
            lines.append(",".join(f'"{cell}"' for cell in row))

        return "\n".join(lines)


@dataclass
class DocumentImage:
    """Extracted image from a document"""

    element_id: str
    page_number: int
    image_url: Optional[str] = None
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


# Helper function for robust document type checking across different import contexts
def is_document_instance(obj: Any) -> bool:
    """
    Check if an object is a Document instance.
    This is more robust than isinstance() when dealing with different import contexts.

    Args:
        obj: Object to check

    Returns:
        bool: True if obj is a Document instance
    """
    return (
        hasattr(obj, "__class__")
        and obj.__class__.__name__ == "Document"
        and obj.__class__.__module__ == "cerevox.document_loader"
    )


class Document:
    """
    Parsed document with enhanced features
    """

    def __init__(
        self,
        content: str,
        metadata: DocumentMetadata,
        tables: Optional[List[DocumentTable]] = None,
        images: Optional[List[DocumentImage]] = None,
        elements: Optional[List[DocumentElement]] = None,
        raw_response: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.metadata = metadata
        self.tables = tables or []
        self.images = images or []
        self.elements = elements or []  # Raw elements from API
        self.raw_response = raw_response or {}

    # Properties for backward compatibility and ease of use
    @property
    def filename(self) -> str:
        """Get the document filename"""
        return self.metadata.filename

    @property
    def file_type(self) -> Optional[str]:
        """Get the document file type"""
        return self.metadata.file_type

    @property
    def page_count(self) -> Optional[int]:
        """Get the number of pages in the document"""
        return self.metadata.total_pages

    @property
    def text(self) -> str:
        """Get the full text content (alias for content)"""
        return self.content

    @property
    def html_content(self) -> str:
        """Get HTML version of the content (competitive feature)"""
        if self.elements:
            return "\n".join(element.html for element in self.elements if element.html)
        return ""

    @property
    def markdown_content(self) -> str:
        """Get Markdown version of the content (competitive feature)"""
        if self.elements:
            return "\n".join(
                element.markdown for element in self.elements if element.markdown
            )
        return self.to_markdown()

    # Enhanced search and filtering methods
    def get_elements_by_page(self, page_number: int) -> List[DocumentElement]:
        """Get all elements from a specific page"""
        return [
            element for element in self.elements if element.page_number == page_number
        ]

    def get_elements_by_type(self, element_type: str) -> List[DocumentElement]:
        """Get all elements of a specific type (competitive feature)"""
        return [
            element for element in self.elements if element.element_type == element_type
        ]

    def get_tables_by_page(self, page_number: int) -> List[DocumentTable]:
        """Get all tables from a specific page"""
        return [table for table in self.tables if table.page_number == page_number]

    def search_content(
        self, query: str, case_sensitive: bool = False, include_tables: bool = True
    ) -> List[DocumentElement]:
        """
        Search for specific content within the document (competitive feature).

        Args:
            query (str): Search query
            case_sensitive (bool): Whether to perform case-sensitive search
            include_tables (bool): Whether to include table content in search

        Returns:
            List[DocumentElement]: Matching elements
        """
        if not query or not query.strip():
            return []

        search_query = query if case_sensitive else query.lower()
        matching_elements = []

        # Search in elements
        for element in self.elements:
            # Handle None text gracefully
            element_text = element.text or ""
            content = element_text if case_sensitive else element_text.lower()

            if search_query in content:
                matching_elements.append(element)
            elif include_tables and element.element_type == "table":
                # Search in table HTML/markdown if text search didn't match
                html_content = (
                    (element.html or "")
                    if case_sensitive
                    else (element.html or "").lower()
                )
                markdown_content = (
                    (element.markdown or "")
                    if case_sensitive
                    else (element.markdown or "").lower()
                )
                if search_query in html_content or search_query in markdown_content:
                    matching_elements.append(element)

        return matching_elements

    # Enhanced content chunking methods (competitive feature)
    def get_text_chunks(
        self, target_size: int = 500, tolerance: float = 0.1
    ) -> List[str]:
        """
        Get the document content as chunks of target size (competitive feature for vector DB preparation).

        Args:
            target_size (int): Target chunk size in characters (default: 500)
            tolerance (float): Allowed deviation from target size as percentage (default: 0.1 for 10%)

        Returns:
            List[str]: List of text chunks optimized for vector databases
        """
        return chunk_text(self.content, target_size, tolerance)

    def get_markdown_chunks(
        self, target_size: int = 500, tolerance: float = 0.1
    ) -> List[str]:
        """
        Get the document markdown content as chunks of target size (competitive feature for vector DB preparation).

        Args:
            target_size (int): Target chunk size in characters (default: 500)
            tolerance (float): Allowed deviation from target size as percentage (default: 0.1 for 10%)

        Returns:
            List[str]: List of markdown chunks with preserved formatting, optimized for vector databases
        """
        if not self.content.strip():
            return []

        markdown_content = (
            self.markdown_content if self.markdown_content else self.to_markdown()
        )
        return chunk_markdown(markdown_content, target_size, tolerance)

    def get_chunked_elements(
        self, target_size: int = 500, tolerance: float = 0.1, format_type: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        Get document elements as chunks with metadata (competitive feature).

        Args:
            target_size (int): Target chunk size in characters (default: 500)
            tolerance (float): Allowed deviation from target size as percentage (default: 0.1 for 10%)
            format_type (str): Format for chunks - "text", "markdown", or "html"

        Returns:
            List[Dict]: List of chunked elements with metadata for advanced processing
        """
        chunked_elements = []

        for element in self.elements:
            # Get content based on format
            if format_type == "markdown" and element.markdown:
                content = element.markdown
                chunks = chunk_markdown(content, target_size, tolerance)
            elif format_type == "html" and element.html:
                content = element.html
                chunks = chunk_text(
                    content, target_size, tolerance
                )  # HTML treated as text for chunking
            else:
                content = element.text
                chunks = chunk_text(content, target_size, tolerance)

            # Create chunked elements with metadata
            for i, chunk in enumerate(chunks):
                chunked_element = {
                    "content": chunk,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "element_id": element.id,
                    "element_type": element.element_type,
                    "page_number": element.page_number,
                    "format_type": format_type,
                    "original_element_length": len(content),
                    "metadata": {
                        "element_id": element.id,
                        "element_type": element.element_type,
                        "page_number": element.page_number,
                        "filename": element.filename,
                    },
                }
                chunked_elements.append(chunked_element)

        return chunked_elements

    # Competitive export formats
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary format with all data"""
        return {
            "content": self.content,
            "metadata": {
                "filename": self.metadata.filename,
                "file_type": self.metadata.file_type,
                "file_id": self.metadata.file_id,
                "total_pages": self.metadata.total_pages,
                "total_elements": self.metadata.total_elements,
                "created_at": (
                    self.metadata.created_at.isoformat()
                    if self.metadata.created_at
                    else None
                ),
                "mime_type": self.metadata.mime_type,
                "original_mime_type": self.metadata.original_mime_type,
                "extra": self.metadata.extra,
                "processing_errors": self.get_processing_errors(),
            },
            "tables": [
                {
                    "element_id": table.element_id,
                    "headers": table.headers,
                    "rows": table.rows,
                    "table_index": table.table_index,
                    "page_number": table.page_number,
                    "html": table.html,
                    "markdown": table.markdown,
                }
                for table in self.tables
            ],
            "images": [
                {
                    "element_id": image.element_id,
                    "page_number": image.page_number,
                    "caption": image.caption,
                    "alt_text": image.alt_text,
                    "image_url": image.image_url,
                    "width": image.width,
                    "height": image.height,
                }
                for image in self.images
            ],
            "elements": [
                {
                    "id": element.id,
                    "element_type": element.element_type,
                    "content": {
                        "html": element.content.html,
                        "markdown": element.content.markdown,
                        "text": element.content.text,
                    },
                    "page_number": element.page_number,
                    "source": {
                        "file": {
                            "extension": element.source.file.extension,
                            "id": element.source.file.id,
                            "index": element.source.file.index,
                            "mime_type": element.source.file.mime_type,
                            "original_mime_type": element.source.file.original_mime_type,
                            "name": element.source.file.name,
                        },
                        "page": {
                            "page_number": element.source.page.page_number,
                            "index": element.source.page.index,
                        },
                        "element": {
                            "characters": element.source.element.characters,
                            "words": element.source.element.words,
                            "sentences": element.source.element.sentences,
                        },
                    },
                }
                for element in self.elements
            ],
        }

    def to_markdown(self) -> str:
        """Enhanced Markdown conversion with proper formatting"""
        lines = [f"# {self.metadata.filename}\n"]

        # Add metadata section
        if self.metadata.total_pages or self.metadata.total_elements:
            lines.append("## Document Info\n")
            if self.metadata.total_pages:
                lines.append(f"- **Pages:** {self.metadata.total_pages}")
            if self.metadata.file_type:
                lines.append(f"- **Type:** {self.metadata.file_type}")
            if self.metadata.total_elements:
                lines.append(f"- **Elements:** {self.metadata.total_elements}")
            lines.append("")

        lines.append("## Content\n")

        # Use enhanced markdown from elements if available
        if self.elements:
            for element in self.elements:
                if element.markdown:
                    lines.append(element.markdown)
                    lines.append("")
        else:
            # Fallback to basic content
            lines.append(self.content)

        return "\n".join(lines)

    def to_html(self) -> str:
        """Convert document to HTML format (competitive feature)"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{self.metadata.filename}</title>",
            "<meta charset='UTF-8'>",
            "</head>",
            "<body>",
            f"<h1>{self.metadata.filename}</h1>",
            "<div class='document-content'>",
        ]

        if self.elements:
            for element in self.elements:
                if element.html:
                    html_parts.append(
                        f"<div class='element element-{element.element_type}'>"
                    )
                    html_parts.append(element.html)
                    html_parts.append(END_DIV)
        else:
            # Fallback to plain text in paragraphs
            paragraphs = self.content.split("\n\n")
            for paragraph in paragraphs:
                if paragraph.strip():
                    html_parts.append(f"<p>{paragraph.strip()}</p>")

        html_parts.extend([END_DIV, "</body>", "</html>"])
        return "\n".join(html_parts)

    def to_pandas_tables(self) -> List["pandas.DataFrame"]:
        """Convert all tables to pandas DataFrames (competitive feature)"""
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for to_pandas_tables(). Install with: pip install pandas"
            )

        return [table.to_pandas() for table in self.tables if table.rows]

    def extract_table_data(self) -> Dict[str, Any]:
        """Extract structured table data for analysis (competitive feature)"""
        total_rows = sum(len(table.rows) for table in self.tables)

        table_data: Dict[str, Any] = {
            "total_tables": len(self.tables),
            "total_rows": total_rows,
            "tables_by_page": {},
            "table_summaries": [],
        }

        for table in self.tables:
            page = table.page_number or 1
            tables_by_page = table_data["tables_by_page"]
            if page not in tables_by_page:
                tables_by_page[page] = 0
            tables_by_page[page] += 1

            pre_columns = len(table.rows[0]) if table.rows else 0
            columns = len(table.headers) if table.headers else pre_columns

            # Create table summary
            summary = {
                "table_index": table.table_index,
                "page_number": table.page_number,
                "rows": len(table.rows),
                "columns": columns,
                "has_headers": bool(table.headers),
                "caption": table.caption,
            }
            table_summaries = table_data["table_summaries"]
            table_summaries.append(summary)

        return table_data

    def validate(self) -> List[str]:
        """
        Validate the document structure and return list of validation errors.

        Returns:
            List[str]: List of validation error messages
        """
        errors = []

        if not self.metadata:
            errors.append("Document metadata is required")
        elif not self.metadata.filename:
            errors.append("Document filename is required")

        elements_is_list = isinstance(self.elements, list)
        tables_is_list = isinstance(self.tables, list)
        images_is_list = isinstance(self.images, list)

        if not elements_is_list:
            errors.append("Document elements must be a list")

        if not tables_is_list:
            errors.append("Document tables must be a list")

        if not images_is_list:
            errors.append("Document images must be a list")

        # Validate elements only if it's a list
        if elements_is_list:
            for i, element in enumerate(self.elements):
                if not element.id:
                    errors.append(f"Element {i} missing required ID")
                if not element.element_type:
                    errors.append(f"Element {i} missing element_type")
                if not element.content:
                    errors.append(f"Element {i} missing content")

        # Validate tables only if it's a list
        if tables_is_list:
            for i, table in enumerate(self.tables):
                if not table.element_id:
                    errors.append(f"Table {i} missing element_id")
                if not table.headers and not table.rows:
                    errors.append(f"Table {i} has no headers or rows")

        return errors

    @classmethod
    def from_api_response(
        cls,
        response_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        filename: str = "document",
    ) -> "Document":
        """Enhanced parsing of API response format with better error handling"""
        if not response_data:
            # Handle empty response
            metadata = DocumentMetadata(filename=filename, file_type="unknown")
            return cls(content="", metadata=metadata)

        try:
            # Check if this is the list of elements format (from example_response.txt)
            if isinstance(response_data, list):
                # Direct list of elements format
                return cls._from_elements_list(response_data, filename)

            # Check if this is a wrapper with data field containing elements
            elif "data" in response_data and isinstance(response_data["data"], list):
                # API format - data field with elements list
                return cls._from_elements_list(response_data["data"], filename)

            # Check if this is the documents array format
            elif "documents" in response_data:
                # Documents array format - take first document
                documents = response_data["documents"]
                if not documents:
                    metadata = DocumentMetadata(filename=filename, file_type="unknown")
                    return cls(content="", metadata=metadata)
                return cls._from_documents_response(documents[0], filename)

            # Check if this is the test format (direct fields)
            elif "filename" in response_data and "content" in response_data:
                # Test format - direct fields
                return cls._from_direct_response(response_data)
            else:
                # Fallback for unknown format
                warnings.warn(
                    f"Unknown API response format. Creating empty document for: {filename}",
                    UserWarning,
                )
                metadata = DocumentMetadata(filename=filename, file_type="unknown")
                return cls(content="", metadata=metadata)

        except Exception as e:
            # Log the error and return empty document rather than crashing
            warnings.warn(
                f"Error parsing API response for {filename}: {str(e)}. Creating empty document.",
                UserWarning,
            )
            metadata = DocumentMetadata(filename=filename, file_type="unknown")
            return cls(content="", metadata=metadata)

    @classmethod
    def from_completed_file_data(
        cls,
        file_data: Dict[str, Any],
        filename: str = "document",
    ) -> "Document":
        """
        Create Document from CompletedFileData structure (new API response format).

        Args:
            file_data: Dict containing 'data', 'errors', and 'error_count' fields
            filename: Name of the file

        Returns:
            Document object with error information properly stored
        """
        # Extract elements data
        elements_data = file_data.get("data", [])

        # Create document from elements
        if elements_data:
            doc = cls._from_elements_list(elements_data, filename)
        else:
            # Create empty document if no data
            metadata = DocumentMetadata(
                filename=filename, file_type="unknown", total_elements=0
            )
            doc = cls(content="", metadata=metadata)

        # Store error information in document metadata
        if "errors" in file_data or "error_count" in file_data:
            doc.metadata.extra["processing_errors"] = {
                "errors": file_data.get("errors", {}),
                "error_count": file_data.get("error_count", 0),
            }

        return doc

    @classmethod
    def _from_elements_list(
        cls, elements_data: List[Dict[str, Any]], filename: str = "document"
    ) -> "Document":
        """Parse the actual API response"""
        if not elements_data:
            metadata = DocumentMetadata(filename=filename, file_type="unknown")
            return cls(content="", metadata=metadata)

        # Parse elements into DocumentElement objects
        parsed_elements: List[DocumentElement] = []
        content_parts: List[str] = []
        tables: List[DocumentTable] = []

        # Extract metadata from first element with validation
        try:
            first_element = elements_data[0]
            source_info = first_element.get("source", {})
            file_info = source_info.get("file", {})

            # Handle both 'extension' and 'extenstion' (typo in API response)
            file_extension = file_info.get("extension")
            metadata = DocumentMetadata(
                filename=file_info.get("name", filename),
                file_type=file_extension.lstrip(".") if file_extension else "unknown",
                file_id=str(file_info.get("id", "")),
                mime_type=file_info.get("mime_type"),
                original_mime_type=file_info.get("original_mime_type"),
                total_elements=len(elements_data),
            )
        except (AttributeError, KeyError, IndexError, TypeError) as e:
            warnings.warn(
                f"Error extracting metadata from API response: {str(e)}. Using defaults.",
                UserWarning,
            )
            metadata = DocumentMetadata(
                filename=filename,
                file_type="unknown",
                total_elements=len(elements_data),
            )

        for i, element_data in enumerate(elements_data):
            try:
                # Parse content with validation - handle new ContentElement structure
                content_dict = element_data.get("content", {})
                if not content_dict:
                    warnings.warn(f"Element has no content. Skipping.", UserWarning)
                    continue

                element_content = ElementContent(
                    html=content_dict.get("html"),
                    markdown=content_dict.get("markdown"),
                    text=content_dict.get("text"),
                )

                # Parse source info with validation
                source = element_data.get("source", {})
                file_source = source.get("file", {})
                page_source = source.get("page", {})
                element_stats_raw = source.get("element", {})

                # Handle both 'extension' and 'extenstion' (typo in API response)
                file_extension = file_source.get("extension") or file_source.get(
                    "extenstion", ""
                )

                file_info_obj = FileInfo(
                    extension=file_extension,
                    id=str(file_source.get("id", "")),
                    index=file_source.get("index", 0),
                    mime_type=file_source.get("mime_type", ""),
                    original_mime_type=file_source.get("original_mime_type", ""),
                    name=file_source.get("name", ""),
                )

                page_number = page_source.get("page_number", 1)

                page_info_obj = PageInfo(
                    page_number=page_number, index=page_source.get("index", 0)
                )

                # Calculate element statistics if missing or zero
                text_content = element_content.text or ""
                characters = element_stats_raw.get("characters", 0)
                words = element_stats_raw.get("words", 0)
                sentences = element_stats_raw.get("sentences", 0)

                # Recalculate if stats are missing or zero
                if not characters and text_content:
                    characters = len(text_content)
                if not words and text_content:
                    words = len(text_content.split())
                if not sentences and text_content:
                    sentences = len(re.split(SENTENCE_REGEX, text_content.strip()))

                element_stats_obj = ElementStats(
                    characters=characters, words=words, sentences=sentences
                )

                source_info_obj = SourceInfo(
                    file=file_info_obj, page=page_info_obj, element=element_stats_obj
                )

                # Create DocumentElement
                element = DocumentElement(
                    content=element_content,
                    element_type=element_data.get("element_type", "unknown"),
                    id=element_data.get("id", str(uuid.uuid4())),
                    source=source_info_obj,
                )

                parsed_elements.append(element)

                # Add text content to content parts
                if element.text:
                    content_parts.append(element.text)

                # Parse tables with better error handling
                if element.element_type == "table" and element.html:
                    try:
                        table = cls._parse_table_from_html(
                            element.html,
                            table_index=len(tables),
                            page_number=element.page_number,
                            element_id=element.id,
                            html_raw=element.html,
                            markdown=element.markdown,
                        )
                        if table:
                            tables.append(table)
                    except Exception as table_error:
                        warnings.warn(
                            f"Error parsing table from element {element.id}: {str(table_error)}",
                            UserWarning,
                        )

            except Exception as e:
                # Skip malformed elements but continue processing
                warnings.warn(
                    f"Warning: Skipping malformed element {i}: {str(e)}", UserWarning
                )
                continue

        # Update metadata with derived info
        if parsed_elements:
            try:
                max_page = max(elem.page_number for elem in parsed_elements)
                metadata.total_pages = max_page
            except (ValueError, TypeError):
                metadata.total_pages = 1

        # Combine all text content
        full_content = "\n\n".join(content_parts)

        doc = cls(
            content=full_content,
            metadata=metadata,
            tables=tables,
            images=[],  # Will be added when image parsing is implemented
            elements=parsed_elements,
            raw_response={"data": elements_data} if elements_data else None,
        )
        return doc

    @classmethod
    def _from_documents_response(
        cls, document_data: Dict[str, Any], filename: str
    ) -> "Document":
        """Parse documents array format"""
        # Validate required fields
        if not document_data:
            raise ValueError("Document data cannot be empty")

        # Extract basic metadata
        doc_filename = document_data.get("filename", filename)
        file_type = document_data.get("file_type", "unknown")
        content = document_data.get("content", "")

        # Extract nested metadata if present
        metadata_dict = document_data.get("metadata", {})

        metadata = DocumentMetadata(
            filename=doc_filename,
            file_type=file_type,
            total_pages=metadata_dict.get("total_pages"),
            total_elements=metadata_dict.get("total_elements"),
        )

        return cls(content=content, metadata=metadata)

    @classmethod
    def _from_direct_response(cls, response_data: Dict[str, Any]) -> "Document":
        """Parse direct response format (used in tests)"""
        # Check for invalid format with "documents" key
        if "documents" in response_data:
            raise ValueError(
                "Direct response format should not contain 'documents' key"
            )

        # Validate required fields for direct format
        if "filename" not in response_data or "content" not in response_data:
            raise KeyError(
                "Direct response format requires 'filename' and 'content' fields"
            )

        # Extract basic metadata
        filename = response_data["filename"]
        file_type = response_data.get("file_type", "unknown")
        content = response_data["content"]

        metadata = DocumentMetadata(
            filename=filename,
            file_type=file_type,
            total_pages=response_data.get("total_pages"),
            total_elements=response_data.get("total_elements"),
        )

        # Parse elements if present
        elements: List[DocumentElement] = []
        tables: List[DocumentTable] = []
        images: List[DocumentImage] = []

        if "elements" in response_data:
            for i, element_data in enumerate(response_data["elements"]):
                element_id = element_data.get("element_id", str(uuid.uuid4()))
                element_type = element_data.get("element_type", "unknown")
                content_dict = element_data.get("content", {})
                page_number = element_data.get("page_number", 1)

                # Create ElementContent
                element_content = ElementContent(
                    html=content_dict.get("html"),
                    markdown=content_dict.get("markdown"),
                    text=content_dict.get("text"),
                )

                # Create SourceInfo with default values
                source_info = SourceInfo(
                    file=FileInfo(
                        extension=element_data.get("file_extension", file_type),
                        id=element_data.get("source_file_id", ""),
                        index=element_data.get("file_index", 0),
                        mime_type=element_data.get("mime_type", "unknown"),
                        original_mime_type=element_data.get(
                            "original_mime_type", "unknown"
                        ),
                        name=filename,
                    ),
                    page=PageInfo(page_number=page_number, index=i),
                    element=ElementStats(
                        characters=len(content_dict.get("text", "")),
                        words=len(content_dict.get("text", "").split()),
                        sentences=len(
                            re.split(SENTENCE_REGEX, content_dict.get("text", ""))
                        ),
                    ),
                )

                # Create DocumentElement
                doc_element = DocumentElement(
                    content=element_content,
                    element_type=element_type,
                    id=element_id,
                    source=source_info,
                )
                elements.append(doc_element)

                # Parse tables
                if element_type == "table" and content_dict.get("html"):
                    table = cls._parse_table_from_html(
                        content_dict.get("html", ""),
                        table_index=len(tables),
                        page_number=page_number,
                        element_id=element_id,
                        html_raw=content_dict.get("html"),
                        markdown=content_dict.get("markdown"),
                    )
                    if table:
                        tables.append(table)

        return cls(
            content=content,
            metadata=metadata,
            tables=tables,
            images=images,
            elements=elements,
            raw_response=response_data,
        )

    @staticmethod
    def _is_tag_instance(element: Any) -> "TypeGuard[Tag]":
        """Check if element is a Tag instance"""
        return isinstance(element, Tag)

    @staticmethod
    def _parse_table_from_html(
        html: str,
        table_index: int,
        page_number: int,
        element_id: str,
        html_raw: Optional[str] = None,
        markdown: Optional[str] = None,
    ) -> Optional[DocumentTable]:
        """Parse table from HTML content using BeautifulSoup"""
        if not BS4_AVAILABLE:
            return None  # Gracefully handle missing beautifulsoup4

        if not html.strip():
            return None

        try:
            soup = BeautifulSoup(html, "html.parser")
            table_element = soup.find("table")
        except Exception:
            # Return None for malformed HTML that can't be parsed
            return None

        if not table_element or not isinstance(table_element, Tag):
            return None

        # Extract headers - only if we find actual th elements
        headers: List[str] = []
        header_row = table_element.find("tr")
        if header_row and isinstance(header_row, Tag):
            # Check if this row has th elements (actual headers)
            th_cells = header_row.find_all("th")
            if th_cells:
                headers = [
                    cell.get_text(strip=True)
                    for cell in th_cells
                    if isinstance(cell, Tag)
                ]

        # Extract rows
        rows: List[List[str]] = []
        all_rows = table_element.find_all("tr")
        # If we found headers (th elements), skip the first row, otherwise include all rows
        start_index = 1 if headers else 0

        for row in all_rows[start_index:]:
            if Document._is_tag_instance(row):
                cells = row.find_all(["td", "th"])
                row_data = [
                    cell.get_text(strip=True) for cell in cells if isinstance(cell, Tag)
                ]
                if row_data:  # Only add non-empty rows
                    rows.append(row_data)

        # Return None if both headers and rows are empty (empty table)
        if not headers and not rows:
            return None

        # Extract caption if present
        caption = None
        caption_element = table_element.find("caption")
        if caption_element and isinstance(caption_element, Tag):
            caption = caption_element.get_text(strip=True)

        return DocumentTable(
            element_id=element_id,
            headers=headers,
            rows=rows,
            page_number=page_number,
            html=html_raw or html,
            markdown=markdown,
            table_index=table_index,
            caption=caption,
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive document statistics (competitive feature)

        Returns:
            Dict[str, Any]: Document statistics including content analysis
        """
        stats: Dict[str, Any] = {
            "filename": self.filename,
            "file_type": self.file_type,
            "total_pages": self.page_count or 0,
            "total_elements": len(self.elements),
            "total_tables": len(self.tables),
            "total_images": len(self.images),
            "content_length": len(self.content),
            "element_types": {},
            "elements_per_page": {},
            "tables_per_page": {},
            "word_count": len(self.content.split()) if self.content else 0,
            "average_words_per_element": 0,
            "table_statistics": {},
        }

        # Element type distribution
        element_types: Dict[str, int] = stats["element_types"]
        elements_per_page: Dict[int, int] = stats["elements_per_page"]

        for element in self.elements:
            element_type = element.element_type
            element_types[element_type] = element_types.get(element_type, 0) + 1

            # Elements per page
            page_num = element.page_number
            elements_per_page[page_num] = elements_per_page.get(page_num, 0) + 1

        # Calculate average words per element
        if self.elements:
            total_words = sum(
                element.source.element.words
                for element in self.elements
                if element.source.element.words
            )
            stats["average_words_per_element"] = (
                total_words / len(self.elements) if total_words > 0 else 0
            )

        # Tables per page
        tables_per_page: Dict[int, int] = stats["tables_per_page"]
        for table in self.tables:
            page_num = table.page_number
            tables_per_page[page_num] = tables_per_page.get(page_num, 0) + 1

        # Table statistics
        if self.tables:
            table_rows = [len(table.rows) for table in self.tables if table.rows]
            table_cols = [
                (
                    len(table.headers)
                    if table.headers
                    else (len(table.rows[0]) if table.rows else 0)
                )
                for table in self.tables
            ]

            stats["table_statistics"] = {
                "total_tables": len(self.tables),
                "total_rows": sum(table_rows),
                "total_columns": sum(table_cols),
                "average_rows_per_table": (
                    sum(table_rows) / len(table_rows) if table_rows else 0
                ),
                "average_columns_per_table": (
                    sum(table_cols) / len(table_cols) if table_cols else 0
                ),
                "largest_table_rows": max(table_rows) if table_rows else 0,
                "largest_table_columns": max(table_cols) if table_cols else 0,
            }

        return stats

    def get_content_by_page(self, page_number: int, format_type: str = "text") -> str:
        """
        Get all content from a specific page in the specified format.

        Args:
            page_number (int): Page number to extract content from
            format_type (str): Format type - "text", "markdown", or "html"

        Returns:
            str: Combined content from the page
        """
        page_elements = self.get_elements_by_page(page_number)

        if not page_elements:
            return ""

        content_parts = []
        for element in page_elements:
            if format_type == "markdown" and element.markdown:
                content_parts.append(element.markdown)
            elif format_type == "html" and element.html:
                content_parts.append(element.html)
            else:
                content_parts.append(element.text or "")

        return "\n\n".join(content_parts)

    def extract_key_phrases(
        self, min_length: int = 3, max_phrases: int = 20
    ) -> List[Tuple[str, int]]:
        """
        Extract key phrases from document content (basic implementation).

        Args:
            min_length (int): Minimum phrase length in characters
            max_phrases (int): Maximum number of phrases to return

        Returns:
            List[Tuple[str, int]]: List of (phrase, frequency) tuples sorted by frequency
        """
        if not self.content:
            return []

        # Simple phrase extraction based on common patterns

        # Extract potential phrases (sequences of words)
        text = self.content.lower()
        # Remove special characters but keep spaces and basic punctuation
        cleaned_text = re.sub(r"[^\w\s\-.]", " ", text)

        # Extract n-grams (2-4 words)
        words = cleaned_text.split()
        phrases = []

        for n in range(2, 5):  # 2-gram to 4-gram
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i : i + n])
                if len(phrase) >= min_length and not phrase.isdigit():
                    phrases.append(phrase)

        # Count frequency and return top phrases
        phrase_counts = Counter(phrases)

        # Filter out very common words/phrases
        stop_phrases = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "man",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "its",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
        }

        filtered_phrases = [
            (phrase, count)
            for phrase, count in phrase_counts.items()
            if phrase not in stop_phrases and count > 1
        ]

        return sorted(filtered_phrases, key=lambda x: x[1], reverse=True)[:max_phrases]

    def get_reading_time(self, words_per_minute: int = 200) -> Dict[str, Any]:
        """
        Estimate reading time for the document.

        Args:
            words_per_minute (int): Average reading speed

        Returns:
            Dict[str, Any]: Reading time estimates
        """
        if not self.content:
            return {"minutes": 0, "seconds": 0, "total_seconds": 0, "word_count": 0}

        word_count = len(self.content.split())
        total_seconds = (word_count / words_per_minute) * 60
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)

        return {
            "minutes": minutes,
            "seconds": seconds,
            "total_seconds": int(total_seconds),
            "word_count": word_count,
            "words_per_minute": words_per_minute,
        }

    def get_language_info(self) -> Dict[str, Any]:
        """
        Basic language detection and analysis (simple implementation).

        Returns:
            Dict[str, Any]: Language information
        """
        if not self.content:
            return {
                "language": "unknown",
                "confidence": 0.0,
                "character_distribution": {},
            }

        # Simple character-based language detection
        import string

        text = self.content.lower()
        char_counts: Dict[str, int] = {}
        total_chars = 0

        for char in text:
            if char.isalpha():
                char_counts[char] = char_counts.get(char, 0) + 1
                total_chars += 1

        # Calculate character distribution
        char_distribution: Dict[str, float] = {}
        for char, count in char_counts.items():
            char_distribution[char] = count / total_chars if total_chars > 0 else 0

        # Simple heuristics for English detection
        english_indicators = ["e", "t", "a", "o", "i", "n", "s", "h", "r"]
        english_score = sum(
            char_distribution.get(char, 0) for char in english_indicators
        )

        # Basic language guess
        if english_score > 0.5:
            language = "english"
            confidence = min(english_score, 1.0)
        else:
            language = "unknown"
            confidence = 0.0

        return {
            "language": language,
            "confidence": confidence,
            "character_distribution": dict(
                sorted(char_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "total_characters": total_chars,
        }

    def get_processing_errors(self) -> Any:
        """
        Get processing error information for this document.

        Returns:
            Dict containing error information from the processing job
        """
        return self.metadata.extra.get(
            "processing_errors", {"errors": {}, "error_count": 0}
        )

    def has_processing_errors(self) -> Any:
        """
        Check if this document had any processing errors.

        Returns:
            True if there were processing errors, False otherwise
        """
        error_info = self.get_processing_errors()
        return error_info.get("error_count", 0) > 0

    def get_error_summary(self) -> str:
        """
        Get a human-readable summary of processing errors for this document.

        Returns:
            String summary of processing errors
        """
        error_info = self.get_processing_errors()
        error_count = error_info.get("error_count", 0)

        if error_count == 0:
            return "No processing errors"

        errors = error_info.get("errors", {})

        error_messages = []
        for location, message in errors.items():
            error_messages.append(f"{location}: {message}")

        return f"{error_count} processing error(s): " + "; ".join(error_messages)


class DocumentBatch:
    """
    Batch of documents with competitive analysis features
    """

    def __init__(self, documents: List[Document]):
        self.documents = documents

    def __len__(self) -> int:
        return len(self.documents)

    def __iter__(self) -> Iterator[Document]:
        return iter(self.documents)

    def __getitem__(self, index: Union[int, str]) -> Document:
        if isinstance(index, int):
            return self.documents[index]
        elif isinstance(index, str):
            # Search by filename
            for doc in self.documents:
                if doc.filename == index:
                    return doc
            raise KeyError(f"Document with filename '{index}' not found")
        else:
            raise TypeError("Index must be int or str")

    # Enhanced batch properties
    @property
    def filenames(self) -> List[str]:
        """Get list of all document filenames"""
        return [doc.filename for doc in self.documents]

    @property
    def file_types(self) -> Dict[str, int]:
        """Get distribution of file types (competitive analysis feature)"""
        type_counts: Dict[str, int] = {}
        for doc in self.documents:
            file_type = doc.file_type or "unknown"
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        return type_counts

    @property
    def total_pages(self) -> int:
        """Get total pages across all documents"""
        return sum(doc.page_count or 0 for doc in self.documents)

    @property
    def total_content_length(self) -> int:
        """Get total character count across all documents"""
        return sum(len(doc.content) for doc in self.documents)

    @property
    def total_tables(self) -> int:
        """Get total number of tables across all documents (competitive feature)"""
        return sum(len(doc.tables) for doc in self.documents)

    # Enhanced search and filtering
    def search_all(
        self, query: str, case_sensitive: bool = False, include_tables: bool = True
    ) -> List[Tuple[Document, List[DocumentElement]]]:
        """Search across all documents in the batch (competitive feature)"""
        results = []
        for doc in self.documents:
            matches = doc.search_content(query, case_sensitive, include_tables)
            if matches:  # Only include documents with matches
                results.append((doc, matches))
        return results

    def filter_by_type(self, file_type: str) -> "DocumentBatch":
        """Filter documents by file type"""
        filtered_docs = [doc for doc in self.documents if doc.file_type == file_type]
        return DocumentBatch(filtered_docs)

    def filter_by_page_count(
        self, min_pages: Optional[int] = None, max_pages: Optional[int] = None
    ) -> "DocumentBatch":
        """
        Filter documents by page count range

        Args:
            min_pages: Minimum page count (inclusive)
            max_pages: Maximum page count (inclusive)
        """
        filtered_docs = []
        for doc in self.documents:
            page_count = doc.page_count or 0
            if min_pages is not None and page_count < min_pages:
                continue
            if max_pages is not None and page_count > max_pages:
                continue
            filtered_docs.append(doc)
        return DocumentBatch(filtered_docs)

    def get_all_tables(self) -> List[Tuple[Document, DocumentTable]]:
        """Get all tables from all documents with their source documents"""
        tables = []
        for doc in self.documents:
            for table in doc.tables:
                tables.append((doc, table))
        return tables

    def get_all_pandas_tables(self) -> List[Tuple[str, "pandas.DataFrame"]]:
        """Convert all tables to pandas DataFrames with filenames (competitive feature)"""
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for get_all_pandas_tables(). Install with: pip install pandas"
            )

        dataframes = []
        for doc in self.documents:
            for i, table in enumerate(doc.tables):
                if table.rows:
                    df = table.to_pandas()
                    table_name = f"{doc.filename}_table_{i}"
                    dataframes.append((table_name, df))
        return dataframes

    def to_combined_text(self, separator: str = "\n\n---\n\n") -> str:
        """Combine all document text into a single string"""
        return separator.join([doc.content for doc in self.documents])

    def to_combined_markdown(self, include_toc: bool = True) -> str:
        """Convert all documents to combined markdown with table of contents"""
        lines = []

        if include_toc:
            lines.append("## Table of Contents\n")  # Changed from "# Table of Contents"
            for i, doc in enumerate(self.documents, 1):
                # Create anchor-friendly filename
                anchor = (
                    doc.filename.lower()
                    .replace(" ", "")
                    .replace(".", "")
                    .replace("_", "")
                    .replace("-", "")
                )
                lines.append(f"{i}. [{doc.filename}](#{anchor})")
            lines.append("\n---\n")

        # Add document content
        for doc in self.documents:
            # Create anchor-friendly filename for heading
            lines.append(f"# {doc.filename}")
            lines.append("\n## Document Info\n")

            if doc.page_count:
                lines.append(f"- **Pages:** {doc.page_count}")
            if doc.file_type:
                lines.append(f"- **Type:** {doc.file_type}")

            lines.append("\n## Content\n")
            lines.append(doc.content)
            lines.append("\n---\n")

        return "\n".join(lines)

    def to_combined_html(self, include_css: bool = True) -> str:
        """Convert all documents to combined HTML"""
        html_parts = []

        # Add proper HTML structure
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html>")
        html_parts.append("<head>")
        html_parts.append("<meta charset='utf-8'>")
        html_parts.append("<title>Document Batch</title>")

        if include_css:
            css = """<style>
.document { margin-bottom: 2rem; border-bottom: 1px solid #ccc; padding-bottom: 1rem; }
.element-table { margin: 1rem 0; }
.element-paragraph { margin: 0.5rem 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; }
</style>"""
            html_parts.append(css)

        html_parts.append("</head>")
        html_parts.append("<body>")
        html_parts.append("<div class='document-batch'>")

        for doc in self.documents:
            # Create safe ID from filename
            doc_id = doc.filename.replace(" ", ".").replace("/", "_").replace("\\", "_")
            html_parts.append(f"<div class='document' id='{doc_id}'>")
            html_parts.append(f"<h1>{doc.filename}</h1>")
            html_parts.append("<div class='document-content'>")

            if doc.content:
                # Convert content to simple HTML paragraphs
                paragraphs = doc.content.split("\n\n")
                for paragraph in paragraphs:
                    if paragraph.strip():
                        html_parts.append(f"<p>{paragraph.strip()}</p>")

            html_parts.append(END_DIV)
            html_parts.append(END_DIV)

        html_parts.append(END_DIV)
        html_parts.append("</body>")
        html_parts.append("</html>")
        return "\n".join(html_parts)

    def get_all_text_chunks(
        self,
        target_size: int = 500,
        tolerance: float = 0.1,
        include_metadata: bool = False,
    ) -> Union[List[str], List[Dict[str, Any]]]:
        """Get text chunks from all documents (competitive feature)"""
        if include_metadata:
            all_chunks: List[Dict[str, Any]] = []
            for doc in self.documents:
                chunks = doc.get_text_chunks(target_size, tolerance)
                for i, chunk in enumerate(chunks):
                    chunk_with_metadata = {
                        "content": chunk,
                        "metadata": {
                            "filename": doc.filename,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "document_index": self.documents.index(doc),
                        },
                    }
                    all_chunks.append(chunk_with_metadata)
            return all_chunks
        else:
            all_chunks_str: List[str] = []
            for doc in self.documents:
                chunks = doc.get_text_chunks(target_size, tolerance)
                all_chunks_str.extend(chunks)
            return all_chunks_str

    def get_all_markdown_chunks(
        self,
        target_size: int = 500,
        tolerance: float = 0.1,
        include_metadata: bool = False,
    ) -> Union[List[str], List[Dict[str, Any]]]:
        """Get markdown chunks from all documents"""
        if include_metadata:
            all_chunks: List[Dict[str, Any]] = []
            for doc in self.documents:
                chunks = doc.get_markdown_chunks(target_size, tolerance)
                for i, chunk in enumerate(chunks):
                    chunk_with_metadata = {
                        "content": chunk,
                        "metadata": {
                            "filename": doc.filename,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "document_index": self.documents.index(doc),
                        },
                    }
                    all_chunks.append(chunk_with_metadata)
            return all_chunks
        else:
            all_chunks_str: List[str] = []
            for doc in self.documents:
                chunks = doc.get_markdown_chunks(target_size, tolerance)
                all_chunks_str.extend(chunks)
            return all_chunks_str

    def get_combined_chunks(
        self, target_size: int = 500, tolerance: float = 0.1, format_type: str = "text"
    ) -> List[str]:
        """Get chunks from all documents combined"""
        if format_type == "markdown":
            result = self.get_all_markdown_chunks(
                target_size, tolerance, include_metadata=False
            )
            return result  # type: ignore
        else:
            result = self.get_all_text_chunks(
                target_size, tolerance, include_metadata=False
            )
            return result  # type: ignore

    def to_dict(self) -> Dict[str, Any]:
        """Convert document batch to dictionary format"""
        return {
            "metadata": {
                "total_documents": len(self.documents),
                "total_pages": self.total_pages,
                "total_content_length": self.total_content_length,
                "total_tables": self.total_tables,
                "total_elements": sum(len(doc.elements) for doc in self.documents),
                "file_types": self.file_types,
            },
            "documents": [doc.to_dict() for doc in self.documents],
        }

    def save_to_json(self, filepath: Union[str, Path], indent: int = 2) -> None:
        """Save batch to JSON file with pretty formatting"""
        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=indent, ensure_ascii=False)

    def export_tables_to_csv(self, output_dir: Union[str, Path]) -> List[str]:
        """Export all tables to separate CSV files (competitive feature)"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        exported_files = []
        for doc in self.documents:
            for i, table in enumerate(doc.tables):
                if table.rows:
                    filename = f"{doc.filename}_table_{i+1}.csv"
                    filepath = output_dir / filename

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(table.to_csv_string())

                    exported_files.append(str(filepath))

        return exported_files

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive batch statistics (competitive feature)"""
        stats = {
            "document_count": len(self.documents),
            "total_pages": self.total_pages,
            "total_content_length": self.total_content_length,
            "total_tables": self.total_tables,
            "total_elements": sum(len(doc.elements) for doc in self.documents),
            "file_types": self.file_types,
            "page_distribution": {},
            "element_distribution": {},
            "content_length_distribution": {},
            "average_metrics": {},
            "error_statistics": self.get_error_statistics(),
        }

        # Page distribution
        page_counts = [doc.page_count or 0 for doc in self.documents]
        if page_counts:
            stats["page_distribution"] = {
                "min": min(page_counts),
                "max": max(page_counts),
                "average": sum(page_counts) / len(page_counts),
                "median": sorted(page_counts)[len(page_counts) // 2],
            }

        # Element distribution
        element_counts = [len(doc.elements) for doc in self.documents]
        if element_counts:
            stats["element_distribution"] = {
                "min": min(element_counts),
                "max": max(element_counts),
                "average": sum(element_counts) / len(element_counts),
                "median": sorted(element_counts)[len(element_counts) // 2],
            }

        # Content length distribution
        content_lengths = [len(doc.content) for doc in self.documents]
        if content_lengths:
            stats["content_length_distribution"] = {
                "min": min(content_lengths),
                "max": max(content_lengths),
                "average": sum(content_lengths) / len(content_lengths),
                "median": sorted(content_lengths)[len(content_lengths) // 2],
            }

        # Table distribution
        table_counts = [len(doc.tables) for doc in self.documents]
        if table_counts:
            stats["table_distribution"] = {
                "min": min(table_counts),
                "max": max(table_counts),
                "average": sum(table_counts) / len(table_counts),
                "median": sorted(table_counts)[len(table_counts) // 2],
                "documents_with_tables": sum(1 for count in table_counts if count > 0),
            }

        # Calculate average metrics across all documents
        if self.documents:
            total_words = sum(
                len(doc.content.split()) for doc in self.documents if doc.content
            )
            total_elements: int = stats["total_elements"]  # type: ignore
            stats["average_metrics"] = {
                "words_per_document": total_words / len(self.documents),
                "pages_per_document": self.total_pages / len(self.documents),
                "elements_per_document": total_elements / len(self.documents),
                "tables_per_document": self.total_tables / len(self.documents),
            }

        return stats

    def validate(self) -> List[str]:
        """
        Validate the document batch structure and return list of validation errors.

        Returns:
            List[str]: List of validation error messages
        """
        errors = []

        if not isinstance(self.documents, list):
            errors.append("DocumentBatch must contain a list of documents")
            return errors

        if not self.documents:
            errors.append("DocumentBatch cannot be empty")
            return errors

        # Validate each document
        valid_documents = []
        for i, doc in enumerate(self.documents):
            # Use helper function for robust type checking across different import contexts
            if not is_document_instance(doc):
                errors.append(
                    f"Document {i} is not a Document instance (got {type(doc).__name__})"
                )
                continue

            valid_documents.append(doc)
            # Validate individual document
            doc_errors = doc.validate()
            for error in doc_errors:
                errors.append(f"Document {i} ({doc.filename}): {error}")

        # Check for duplicate filenames only among valid Document instances
        filenames = [doc.filename for doc in valid_documents]
        seen_filenames = set()
        for i, filename in enumerate(filenames):
            if filename in seen_filenames:
                errors.append(f"Duplicate filename found: {filename} (document {i})")
            seen_filenames.add(filename)

        return errors

    def get_documents_by_element_type(self, element_type: str) -> "DocumentBatch":
        """
        Filter documents that contain elements of a specific type.

        Args:
            element_type (str): Element type to filter by

        Returns:
            DocumentBatch: New batch containing only documents with the specified element type
        """
        filtered_docs = []
        for doc in self.documents:
            if any(element.element_type == element_type for element in doc.elements):
                filtered_docs.append(doc)
        return DocumentBatch(filtered_docs)

    def get_summary(self, max_chars_per_doc: int = 200) -> str:
        """
        Generate a summary of the document batch.

        Args:
            max_chars_per_doc (int): Maximum characters to include from each document

        Returns:
            str: Batch summary
        """
        if not self.documents:
            return "Empty document batch"

        summary_parts = [
            f"Document Batch Summary ({len(self.documents)} documents)",
            "=" * 50,
            f"Total Pages: {self.total_pages}",
            f"Total Content Length: {self.total_content_length:,} characters",
            f"Total Tables: {self.total_tables}",
            f"File Types: {', '.join(f'{k}({v})' for k, v in self.file_types.items())}",
            "",
            "Documents:",
        ]

        for i, doc in enumerate(self.documents, 1):
            doc_preview = (
                doc.content[:max_chars_per_doc] if doc.content else "[No content]"
            )
            if len(doc.content) > max_chars_per_doc:
                doc_preview += "..."

            summary_parts.extend(
                [
                    f"{i}. {doc.filename} ({doc.file_type})",
                    f"   Pages: {doc.page_count or 'N/A'}, Elements: {len(doc.elements)}, Tables: {len(doc.tables)}",
                    f"   Preview: {doc_preview.replace(chr(10), ' ').replace(chr(13), ' ')}",
                    "",
                ]
            )

        return "\n".join(summary_parts)

    def find_documents_with_keyword(
        self, keyword: str, case_sensitive: bool = False
    ) -> List[Tuple[Document, int]]:
        """
        Find documents containing a specific keyword and return with match counts.

        Args:
            keyword (str): Keyword to search for
            case_sensitive (bool): Whether search should be case sensitive

        Returns:
            List[Tuple[Document, int]]: List of (document, match_count) tuples
        """
        results = []
        search_keyword = keyword if case_sensitive else keyword.lower()

        for doc in self.documents:
            content = doc.content if case_sensitive else doc.content.lower()
            match_count = content.count(search_keyword)
            if match_count > 0:
                results.append((doc, match_count))

        # Sort by match count (descending)
        return sorted(results, key=lambda x: x[1], reverse=True)

    def get_content_similarity_matrix(self) -> List[List[float]]:
        """
        Calculate basic content similarity matrix between documents.

        Returns:
            List[List[float]]: Matrix where matrix[i][j] is similarity between document i and j
        """
        if len(self.documents) < 2:
            return [[1.0]]

        def simple_similarity(text1: str, text2: str) -> float:
            """Calculate basic word overlap similarity"""
            if not text1 or not text2:
                return 0.0

            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())

            if not words1 or not words2:
                return 0.0

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            return len(intersection) / len(union) if union else 0.0

        n_docs = len(self.documents)
        similarity_matrix = [[0.0 for _ in range(n_docs)] for _ in range(n_docs)]

        for i in range(n_docs):
            for j in range(n_docs):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                else:
                    similarity = simple_similarity(
                        self.documents[i].content, self.documents[j].content
                    )
                    similarity_matrix[i][j] = similarity

        return similarity_matrix

    @classmethod
    def from_processing_job_response(
        cls, response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract processing information from a job response (for progress tracking).

        Args:
            response_data: Job response data with processing status

        Returns:
            Dict containing processing progress information
        """
        progress_info = {
            "status": response_data.get("status", "unknown"),
            "progress": response_data.get("progress", 0),
            "total_files": response_data.get("total_files", 0),
            "completed_files": response_data.get("completed_files", 0),
            "failed_files": response_data.get("failed_files", 0),
            "processing_files": response_data.get("processing_files", 0),
            "total_chunks": response_data.get("total_chunks", 0),
            "completed_chunks": response_data.get("completed_chunks", 0),
            "failed_chunks": response_data.get("failed_chunks", 0),
            "processing_chunks": response_data.get("processing_chunks", 0),
            "files": {},
        }

        # Extract file-level progress if available
        if "files" in response_data and isinstance(response_data["files"], dict):
            for filename, file_info in response_data["files"].items():
                if isinstance(file_info, dict) and "status" in file_info:
                    progress_info["files"][filename] = {
                        "name": file_info.get("name", filename),
                        "status": file_info.get("status", "unknown"),
                        "total_chunks": file_info.get("total_chunks", 0),
                        "completed_chunks": file_info.get("completed_chunks", 0),
                        "failed_chunks": file_info.get("failed_chunks", 0),
                        "processing_chunks": file_info.get("processing_chunks", 0),
                        "last_updated": file_info.get("last_updated"),
                    }

        return progress_info

    @classmethod
    def from_api_response(
        cls,
        response_data: Union[Dict[str, Any], List[Any]],
        filenames: Optional[List[str]] = None,
    ) -> "DocumentBatch":
        """Create DocumentBatch from API response data with support for new response structure"""
        documents: List[Document] = []

        # Handle case where response_data is a list (direct elements format)
        if isinstance(response_data, list):
            # Direct list of elements - create single document
            doc = Document.from_api_response(response_data) if response_data else None
            documents.append(doc) if doc else None
            return cls(documents)

        # From here, response_data is guaranteed to be a Dict[str, Any]
        # Handle the new completed job response structure with files field
        if "files" in response_data and isinstance(response_data["files"], dict):
            # New format: files field contains CompletedFileData objects by filename
            for filename, file_data in response_data["files"].items():
                try:
                    # Check if this is CompletedFileData (has 'data' field)
                    if isinstance(file_data, dict) and "data" in file_data:
                        # Use new helper method for better handling
                        doc = Document.from_completed_file_data(file_data, filename)
                        documents.append(doc)
                    # Handle FileProcessingInfo objects (for processing jobs)
                    elif isinstance(file_data, dict) and "status" in file_data:
                        # This is processing info, not completed data - skip for now
                        # Could be used for progress tracking in the future
                        continue
                    else:
                        # Fallback: treat as direct elements data
                        if file_data:
                            doc = Document.from_api_response(file_data, filename)
                            documents.append(doc)
                except Exception as e:
                    warnings.warn(
                        f"Error processing file data for {filename}: {str(e)}. Skipping.",
                        UserWarning,
                    )
                    continue

        # Handle legacy formats for backward compatibility
        elif filenames:
            # Multiple files response - legacy format
            for i, filename in enumerate(filenames):
                if i < len(response_data.get("documents", [])):
                    doc_data = response_data["documents"][i]
                    doc = Document.from_api_response(doc_data, filename)
                    documents.append(doc)
        else:
            # Check for various legacy response formats
            if "documents" in response_data:
                for doc_data in response_data["documents"]:
                    doc = Document.from_api_response(doc_data)
                    documents.append(doc)
            elif "results" in response_data:
                # Handle results format (commonly used for batch responses)
                for doc_data in response_data["results"]:
                    doc = Document.from_api_response(doc_data)
                    documents.append(doc)
            elif "data" in response_data:
                # Handle API data response format
                if response_data["data"]:  # Only create document if data is not empty
                    doc = Document.from_api_response(response_data)
                    documents.append(doc)
                # If data is empty, documents list remains empty
            else:
                # Single document - only if response has meaningful content
                # Check if response has actual document data (not just empty structure)
                if response_data and any(
                    key in response_data
                    for key in ["text", "content", "filename", "elements"]
                ):
                    doc = Document.from_api_response(response_data)
                    documents.append(doc)

        return cls(documents)

    @classmethod
    def load_from_json(cls, filepath: Union[str, Path]) -> "DocumentBatch":
        """Load DocumentBatch from JSON file"""
        import json

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        for doc_data in data.get("documents", []):
            # Reconstruct Document from dict data
            metadata_dict = doc_data["metadata"]
            metadata = DocumentMetadata(
                filename=metadata_dict["filename"],
                file_type=metadata_dict["file_type"],
                file_id=metadata_dict.get("file_id"),
                total_pages=metadata_dict.get("total_pages"),
                total_elements=metadata_dict.get("total_elements"),
                created_at=(
                    datetime.fromisoformat(metadata_dict["created_at"])
                    if metadata_dict.get("created_at")
                    else None
                ),
                mime_type=metadata_dict.get("mime_type"),
                original_mime_type=metadata_dict.get("original_mime_type"),
                extra=metadata_dict.get("extra", {}),
            )

            # Reconstruct tables, images, elements
            tables = [
                DocumentTable(**table_data) for table_data in doc_data.get("tables", [])
            ]
            images = [
                DocumentImage(**image_data) for image_data in doc_data.get("images", [])
            ]

            # Reconstruct elements with proper structure
            elements = []
            for element_data in doc_data.get("elements", []):
                content_dict = element_data.get("content", {})
                source_dict = element_data.get("source", {})

                element_content = ElementContent(
                    html=content_dict.get("html"),
                    markdown=content_dict.get("markdown"),
                    text=content_dict.get("text"),
                )

                file_info = FileInfo(**source_dict.get("file", {}))
                page_info = PageInfo(**source_dict.get("page", {}))
                element_stats = ElementStats(**source_dict.get("element", {}))

                source_info = SourceInfo(
                    file=file_info, page=page_info, element=element_stats
                )

                element = DocumentElement(
                    content=element_content,
                    element_type=element_data.get("element_type", "unknown"),
                    id=element_data.get("id", str(uuid.uuid4())),
                    source=source_info,
                )
                elements.append(element)

            doc = Document(
                content=doc_data["content"],
                metadata=metadata,
                tables=tables,
                images=images,
                elements=elements,
            )
            documents.append(doc)

        return cls(documents)

    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive error statistics across all documents in the batch.

        Returns:
            Dict containing error statistics for the entire batch
        """
        total_documents = len(self.documents)
        documents_with_errors = 0
        total_errors = 0
        error_details = {}

        for doc in self.documents:
            error_info = doc.get_processing_errors()
            error_count = error_info.get("error_count", 0)

            if error_count > 0:
                documents_with_errors += 1
                total_errors += error_count

                # Collect error details
                errors = error_info.get("errors", {})
                if errors:
                    error_details[doc.filename] = errors

        return {
            "total_documents": total_documents,
            "documents_with_errors": documents_with_errors,
            "documents_without_errors": total_documents - documents_with_errors,
            "total_errors": total_errors,
            "average_errors_per_document": (
                total_errors / total_documents if total_documents > 0 else 0
            ),
            "error_rate": (
                documents_with_errors / total_documents if total_documents > 0 else 0
            ),
            "error_details": error_details,
        }

    def get_documents_with_errors(self) -> List[Document]:
        """
        Get all documents that had processing errors.

        Returns:
            List of Document objects that had processing errors
        """
        return [doc for doc in self.documents if doc.has_processing_errors()]

    def get_documents_without_errors(self) -> List[Document]:
        """
        Get all documents that had no processing errors.

        Returns:
            List of Document objects that had no processing errors
        """
        return [doc for doc in self.documents if not doc.has_processing_errors()]

    def get_error_summary(self) -> str:
        """
        Get a human-readable summary of processing errors for the entire batch.

        Returns:
            String summary of processing errors across all documents
        """
        stats = self.get_error_statistics()

        if stats["total_errors"] == 0:
            return f"No processing errors in batch of {stats['total_documents']} document(s)"

        summary_parts = [
            f"Processing errors in batch of {stats['total_documents']} document(s):",
            f"- {stats['documents_with_errors']} document(s) with errors",
            f"- {stats['total_errors']} total error(s)",
            f"- {stats['error_rate']:.1%} error rate",
        ]

        if stats["error_details"]:
            summary_parts.append("\nError details:")
            for filename, errors in stats["error_details"].items():
                for location, message in errors.items():
                    summary_parts.append(f"- {filename}[{location}]: {message}")

        return "\n".join(summary_parts)


def chunk_markdown(
    markdown_text: str, target_size: int = 500, tolerance: float = 0.1
) -> List[str]:
    """
    Chunks markdown text at logical boundaries with a target size.

    Improved version with better markdown awareness and more robust splitting.

    Args:
        markdown_text (str): The markdown string to chunk
        target_size (int): Target chunk size in characters (default: 500)
        tolerance (float): Allowed deviation from target size as percentage (default: 0.1 for 10%)

    Returns:
        list: Array of markdown string chunks
    """
    if not markdown_text or not markdown_text.strip():
        return []

    # Calculate size bounds
    min_size = int(target_size * (1 - tolerance))
    max_size = int(target_size * (1 + tolerance))

    chunks = []

    # First, try to split by markdown sections (headers)
    header_sections = _split_by_markdown_sections(markdown_text)

    for section in header_sections:
        if len(section) <= max_size:
            # Section fits within limits
            if section.strip():
                chunks.append(section.strip())
        else:
            # Section is too large, split by paragraphs
            paragraph_chunks = _split_by_paragraphs(section, max_size)
            chunks.extend(paragraph_chunks)

    # Post-process: merge small final chunks if possible
    chunks = _merge_small_chunks(chunks, min_size, max_size)

    return [chunk for chunk in chunks if chunk.strip()]


def chunk_text(text: str, target_size: int = 500, tolerance: float = 0.1) -> List[str]:
    """
    Chunks plain text at logical boundaries with a target size.

    Args:
        text (str): The text string to chunk
        target_size (int): Target chunk size in characters (default: 500)
        tolerance (float): Allowed deviation from target size as percentage (default: 0.1 for 10%)

    Returns:
        list: Array of text string chunks
    """
    if not text or not text.strip():
        return []

    # Calculate size bounds
    min_size = int(target_size * (1 - tolerance))
    max_size = int(target_size * (1 + tolerance))

    # Split by paragraphs for plain text
    chunks = _split_by_paragraphs(text, max_size)

    # Post-process: merge small final chunks if possible
    chunks = _merge_small_chunks(chunks, min_size, max_size)

    return [chunk for chunk in chunks if chunk.strip()]


def _split_text(text: str, pattern: str) -> List[str]:
    """Split text by a given pattern."""
    return text.split(pattern)


def _split_by_markdown_sections(text: str) -> List[str]:
    """Split text by markdown headers, preserving header hierarchy."""
    # Find all markdown headers
    header_pattern = r"^(#{1,6})\s+(.+)$"
    lines = _split_text(text, "\n")

    sections = []
    current_section: List[str] = []

    for line in lines:
        if re.match(header_pattern, line, re.MULTILINE):
            # New header found
            if current_section:
                sections.append("\n".join(current_section))
                current_section = []
        current_section.append(line)

    # Add final section
    if current_section:
        sections.append("\n".join(current_section))

    # If no headers found, return the whole text
    if len(sections) <= 1:
        return [text]

    return sections


def _split_by_paragraphs(text: str, max_size: int) -> List[str]:
    """Split text by paragraphs, respecting markdown structure."""
    # Split by double newlines (paragraph boundaries)
    paragraphs = re.split(r"\n\s*\n", text.strip())
    if not paragraphs:
        return [text] if text.strip() else []

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # Check if adding this paragraph would exceed max_size
        test_chunk = current_chunk + ("\n\n" if current_chunk else "") + paragraph

        if current_chunk:
            if len(test_chunk) <= max_size:
                # Can add this paragraph
                current_chunk = test_chunk
            else:
                chunks.append(current_chunk)

                if len(paragraph) <= max_size:
                    current_chunk = paragraph
                else:
                    # Paragraph is too large, split by sentences
                    sentence_chunks = _split_large_text_by_sentences(
                        paragraph, max_size
                    )
                    chunks.extend(sentence_chunks)
                    current_chunk = ""
        else:
            # First paragraph in chunk
            if len(paragraph) <= max_size:
                current_chunk = paragraph
            else:
                # Single paragraph is too large, split by sentences
                sentence_chunks = _split_large_text_by_sentences(paragraph, max_size)
                chunks.extend(sentence_chunks)

    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _split_large_text_by_sentences(text: str, max_size: int) -> List[str]:
    """Split large text by sentences, preserving markdown formatting."""
    # Handle code blocks specially - don't split them
    if "```" in text:
        return _split_preserving_code_blocks(text, max_size)

    sentences = _split_at_sentences(text)
    if not sentences:
        return [text] if text.strip() else []

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If a single sentence is larger than max_size, we need to split it further
        if len(sentence) > max_size:
            # Add current chunk if it has content
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # Split the oversized sentence by character limit
            char_chunks = _split_by_character_limit(sentence, max_size)
            chunks.extend(char_chunks)
        else:
            # Check if we can add this sentence to current chunk
            test_chunk = current_chunk + (" " if current_chunk else "") + sentence

            if len(test_chunk) <= max_size:
                current_chunk = test_chunk
            else:
                # Current chunk is ready, start new one
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _split_preserving_code_blocks(text: str, max_size: int) -> List[str]:
    """Split text while preserving code blocks intact."""
    # Split by code blocks
    parts = re.split(r"(```[\s\S]*?```)", text)

    chunks = []
    current_chunk = ""

    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            # This is a code block - keep it intact
            if len(current_chunk) + len(part) <= max_size:
                current_chunk += part
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                if len(part) <= max_size:
                    current_chunk = part
                else:
                    # Code block is too large - add as separate chunk
                    chunks.append(part)
                    current_chunk = ""
        else:
            # Regular text - can be split
            if len(current_chunk) + len(part) <= max_size:
                current_chunk += part
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                # Split the text part if it's too large
                if len(part) <= max_size:
                    current_chunk = part
                else:
                    text_chunks = _split_by_character_limit(part, max_size)
                    chunks.extend(text_chunks[:-1])  # Add all but last
                    current_chunk = text_chunks[-1] if text_chunks else ""

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _split_by_character_limit(text: str, max_size: int) -> List[str]:
    """Split text by character limit, trying to break at word boundaries."""
    if len(text) <= max_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_size

        if end >= len(text):
            # Last chunk
            remaining = text[start:].strip()
            chunks.append(remaining) if remaining else None
            break

        # Try to find a good boundary before max_size
        chunk_text = text[start:end]

        # Look for various boundary types in order of preference
        boundaries = [
            chunk_text.rfind("\n\n"),  # Paragraph break
            chunk_text.rfind("\n"),  # Line break
            chunk_text.rfind(". "),  # Sentence end
            chunk_text.rfind("! "),  # Exclamation
            chunk_text.rfind("? "),  # Question
            chunk_text.rfind(", "),  # Comma
            chunk_text.rfind(" "),  # Any space
        ]

        # Find the best boundary
        boundary = -1
        for b in boundaries:
            if b > len(chunk_text) * 0.7:  # Don't break too early
                boundary = b
                break

        if boundary > 0:
            # Good boundary found
            end = start + boundary + 1
            chunk = text[start:end].strip()
            chunks.append(chunk) if chunk else None
            start = end
        else:
            # No good boundary found, hard break
            chunk = text[start:end].strip()
            chunks.append(chunk) if chunk else None
            start = end

    return [chunk for chunk in chunks if chunk.strip()]


def _strip_text(text: str) -> str:
    """Strip text of whitespace and newlines."""
    return text.strip()


def _split_at_sentences(text: str) -> List[str]:
    """Split text at sentence boundaries, preserving markdown formatting."""
    # Common abbreviations to avoid splitting on
    abbreviations = {
        "Dr",
        "Mr",
        "Mrs",
        "Ms",
        "Prof",
        "etc",
        "vs",
        "e.g",
        "i.e",
        "Inc",
        "Ltd",
        "Co",
        "Corp",
        "Ave",
        "St",
        "Rd",
        "Blvd",
        "Dept",
        "Univ",
        "Vol",
        "No",
        "pp",
        "cf",
        "viz",
        "al",
        "et",
        "ibid",
        "op",
        "loc",
        "circa",
        "ca",
        "Fig",
        "Table",
        "Ch",
    }

    # Find all sentence-ending punctuation
    sentence_ends = []

    # Use a more sophisticated pattern that handles markdown
    for match in re.finditer(SENTENCE_REGEX, text):
        start_pos = match.start()
        end_pos = match.end()

        # Check if this is likely an abbreviation
        is_abbreviation = False
        if match.group().startswith("."):
            # Look backward for abbreviations
            word_before = ""
            i = start_pos - 1
            while i >= 0 and text[i].isalnum():
                word_before = text[i] + word_before
                i -= 1

            if word_before in abbreviations or (i >= 0 and text[i] in ["/", "@"]):
                is_abbreviation = True

        # Check what follows
        after_match = text[end_pos:].lstrip()
        if not is_abbreviation and (
            not after_match
            or after_match[0].isupper()
            or after_match[0] in ["#", "-", "*", "+"]
        ):
            sentence_ends.append(end_pos)

    # Split at sentence boundaries
    if not sentence_ends:
        return [text.strip()] if text.strip() else []

    sentences = []
    start = 0

    for end_pos in sentence_ends:
        sentence = _strip_text(text[start:end_pos])
        sentences.append(sentence) if sentence else None
        start = end_pos

    # Add remaining text
    if start < len(text):
        remaining = text[start:].strip()
        if remaining:
            sentences.append(remaining)

    return sentences


def _merge_small_chunks(chunks: List[str], min_size: int, max_size: int) -> List[str]:
    """Merge small chunks with adjacent ones if possible."""
    if len(chunks) <= 1:
        return chunks

    merged = []
    i = 0

    while i < len(chunks):
        current_chunk = chunks[i]

        # If current chunk is small, try to merge with next chunk
        if i < len(chunks) - 1 and len(current_chunk) < min_size:
            next_chunk = chunks[i + 1]
            combined = current_chunk + "\n\n" + next_chunk

            if (
                len(combined) <= max_size * 1.2
            ):  # Allow slight overflow for better semantics
                merged.append(combined)
                i += 2  # Skip next chunk since we merged it
                continue

        # If we're at the last chunk and it's small, try to merge with previous
        if i == len(chunks) - 1 and len(current_chunk) < min_size and merged:
            last_merged = merged[-1]
            combined = last_merged + "\n\n" + current_chunk

            if len(combined) <= max_size * 1.2:  # Allow slight overflow
                merged[-1] = combined
                i += 1
                continue

        # No merge possible, add as is
        merged.append(current_chunk)
        i += 1

    return merged
