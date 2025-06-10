"""
Comprehensive Examples for Cerevox Document Loader

This file demonstrates all the functionality available in the cerevox.document_loader module.

FEATURES DEMONSTRATED:
===================

1. BASIC DOCUMENT OPERATIONS:
   - Loading documents from API responses
   - Accessing document properties (filename, content, metadata)
   - Working with different content formats (text, HTML, markdown)

2. DOCUMENT ELEMENTS:
   - Accessing individual document elements
   - Filtering elements by type and page
   - Working with element content and metadata

3. TABLE EXTRACTION & PROCESSING:
   - Extracting tables from documents
   - Converting tables to pandas DataFrames
   - Exporting tables to CSV format
   - Advanced table analysis and statistics

4. CONTENT SEARCH & FILTERING:
   - Searching content within documents
   - Filtering by various criteria
   - Finding specific element types

5. CONTENT CHUNKING (for Vector DBs):
   - Text chunking with customizable size
   - Markdown-aware chunking
   - Element-based chunking with metadata

6. EXPORT FORMATS:
   - Converting to various formats (dict, markdown, HTML)
   - Saving to JSON files
   - Combined document exports

7. DOCUMENT ANALYSIS:
   - Document statistics and metrics
   - Content analysis (reading time, language info)
   - Key phrase extraction
   - Page-based content extraction

8. BATCH OPERATIONS:
   - Working with multiple documents
   - Batch analysis and statistics
   - Cross-document search and comparison
   - Batch export operations

9. VALIDATION & ERROR HANDLING:
   - Document validation
   - Error handling for malformed data
   - Graceful degradation

10. ADVANCED FEATURES:
    - Content similarity analysis
    - Document comparison
    - Comprehensive statistics
    - Custom formatting options

11. ERROR HANDLING & EDGE CASES:
    - Handle empty API response
    - Handle malformed data gracefully
    - Handle missing optional dependencies
    - Validate document with errors

12. PRACTICAL USAGE PATTERNS:
    - Demonstrate common usage patterns

Let's explore each of these features with practical examples!
"""

import json
import warnings
from pathlib import Path
from typing import Any, Dict, List

# Import the cerevox document loader
from cerevox.document_loader import (
    Document,
    DocumentBatch,
    DocumentElement,
    DocumentMetadata,
    DocumentTable,
    ElementContent,
    chunk_markdown,
    chunk_text,
)

# Suppress warnings for cleaner output in examples
warnings.filterwarnings("ignore")

print("Cerevox Document Loader - Comprehensive Examples")
print("=" * 50)

# ============================================================================
# SAMPLE DATA FOR EXAMPLES
# ============================================================================


def create_sample_api_response():
    """Create a sample API response that mimics the actual API format"""
    return [
        {
            "id": "elem_001",
            "element_type": "paragraph",
            "content": {
                "html": "<p>This is the first paragraph of our sample document. It contains important information about the document structure.</p>",
                "markdown": "This is the first paragraph of our sample document. It contains important information about the document structure.",
                "text": "This is the first paragraph of our sample document. It contains important information about the document structure.",
            },
            "source": {
                "file": {
                    "extension": "pdf",
                    "id": "file_123",
                    "index": 0,
                    "mime_type": "application/pdf",
                    "original_mime_type": "application/pdf",
                    "name": "sample_document.pdf",
                },
                "page": {"page_number": 1, "index": 0},
                "element": {"characters": 115, "words": 20, "sentences": 2},
            },
        },
        {
            "id": "elem_002",
            "element_type": "table",
            "content": {
                "html": "<table><thead><tr><th>Product</th><th>Price</th><th>Quantity</th></tr></thead><tbody><tr><td>Laptop</td><td>$1,200</td><td>5</td></tr><tr><td>Phone</td><td>$800</td><td>12</td></tr><tr><td>Tablet</td><td>$400</td><td>8</td></tr></tbody></table>",
                "markdown": "| Product | Price | Quantity |\n|---------|-------|----------|\n| Laptop  | $1,200| 5        |\n| Phone   | $800  | 12       |\n| Tablet  | $400  | 8        |",
                "text": "Product\tPrice\tQuantity\nLaptop\t$1,200\t5\nPhone\t$800\t12\nTablet\t$400\t8",
            },
            "source": {
                "file": {
                    "extension": "pdf",
                    "id": "file_123",
                    "index": 0,
                    "mime_type": "application/pdf",
                    "original_mime_type": "application/pdf",
                    "name": "sample_document.pdf",
                },
                "page": {"page_number": 1, "index": 1},
                "element": {"characters": 85, "words": 15, "sentences": 1},
            },
        },
        {
            "id": "elem_003",
            "element_type": "paragraph",
            "content": {
                "html": "<p>This is another paragraph on page 2. It discusses the implications of the data presented in the table above.</p>",
                "markdown": "This is another paragraph on page 2. It discusses the implications of the data presented in the table above.",
                "text": "This is another paragraph on page 2. It discusses the implications of the data presented in the table above.",
            },
            "source": {
                "file": {
                    "extension": "pdf",
                    "id": "file_123",
                    "index": 0,
                    "mime_type": "application/pdf",
                    "original_mime_type": "application/pdf",
                    "name": "sample_document.pdf",
                },
                "page": {"page_number": 2, "index": 2},
                "element": {"characters": 96, "words": 18, "sentences": 1},
            },
        },
    ]


# ============================================================================
# 1. BASIC DOCUMENT OPERATIONS
# ============================================================================


def demonstrate_basic_operations():
    """Demonstrate basic document loading and property access"""
    print("\n1. BASIC DOCUMENT OPERATIONS")
    print("-" * 30)

    # Create a document from API response
    sample_data = create_sample_api_response()
    document = Document.from_api_response(sample_data, "sample_document.pdf")

    print("✓ Document loaded from API response")
    print(f"  Filename: {document.filename}")
    print(f"  File type: {document.file_type}")
    print(f"  Total pages: {document.page_count}")
    print(f"  Total elements: {len(document.elements)}")
    print(f"  Content length: {len(document.content)} characters")

    # Access different content formats
    print(f"\n✓ Content formats available:")
    print(f"  Text content: {len(document.text)} chars")
    print(f"  HTML content: {len(document.html_content)} chars")
    print(f"  Markdown content: {len(document.markdown_content)} chars")

    # Show a preview of the content
    print(f"\n✓ Content preview (first 100 chars):")
    print(f"  {document.content[:100]}...")

    return document


# ============================================================================
# 2. DOCUMENT ELEMENTS
# ============================================================================


def demonstrate_document_elements(document):
    """Demonstrate working with document elements"""
    print("\n2. DOCUMENT ELEMENTS")
    print("-" * 20)

    # Access all elements
    print(f"✓ Total elements: {len(document.elements)}")

    # Loop through elements and show their properties
    for i, element in enumerate(document.elements):
        print(f"\n  Element {i+1}:")
        print(f"    ID: {element.id}")
        print(f"    Type: {element.element_type}")
        print(f"    Page: {element.page_number}")
        print(f"    Text length: {len(element.text)} chars")
        print(f"    Preview: {element.text[:50]}...")

    # Filter elements by page
    page_1_elements = document.get_elements_by_page(1)
    page_2_elements = document.get_elements_by_page(2)
    print(f"\n✓ Page filtering:")
    print(f"  Page 1 elements: {len(page_1_elements)}")
    print(f"  Page 2 elements: {len(page_2_elements)}")

    # Filter elements by type
    paragraphs = document.get_elements_by_type("paragraph")
    tables = document.get_elements_by_type("table")
    print(f"\n✓ Type filtering:")
    print(f"  Paragraph elements: {len(paragraphs)}")
    print(f"  Table elements: {len(tables)}")


# ============================================================================
# 3. TABLE EXTRACTION & PROCESSING
# ============================================================================


def demonstrate_table_operations(document):
    """Demonstrate table extraction and processing"""
    print("\n3. TABLE EXTRACTION & PROCESSING")
    print("-" * 33)

    # Access extracted tables
    print(f"✓ Total tables found: {len(document.tables)}")

    if document.tables:
        table = document.tables[0]  # Get first table
        print(f"\n  Table details:")
        print(f"    Element ID: {table.element_id}")
        print(f"    Page: {table.page_number}")
        print(f"    Headers: {table.headers}")
        print(f"    Rows: {len(table.rows)}")
        print(f"    Columns: {len(table.headers) if table.headers else 'N/A'}")

        # Show table data
        print(f"\n  Table data:")
        if table.headers:
            print(f"    Headers: {table.headers}")
        for i, row in enumerate(table.rows):
            print(f"    Row {i+1}: {row}")

        # Convert to CSV
        csv_string = table.to_csv_string()
        print(f"\n✓ CSV format:")
        print(f"    {csv_string[:100]}...")

        # Try to convert to pandas (if available)
        try:
            df = table.to_pandas()
            print(f"\n✓ Pandas DataFrame:")
            print(f"    Shape: {df.shape}")
            print(f"    Columns: {list(df.columns)}")
        except ImportError:
            print(f"\n⚠ Pandas not available for DataFrame conversion")

    # Get table statistics
    table_data = document.extract_table_data()
    print(f"\n✓ Table statistics:")
    print(f"  Total tables: {table_data['total_tables']}")
    print(f"  Total rows: {table_data['total_rows']}")
    print(f"  Tables by page: {table_data['tables_by_page']}")


# ============================================================================
# 4. CONTENT SEARCH & FILTERING
# ============================================================================


def demonstrate_search_and_filtering(document):
    """Demonstrate content search and filtering capabilities"""
    print("\n4. CONTENT SEARCH & FILTERING")
    print("-" * 30)

    # Search for specific content
    search_results = document.search_content("document")
    print(f"✓ Search for 'document': {len(search_results)} matches found")

    for i, element in enumerate(search_results):
        print(f"  Match {i+1}: {element.element_type} on page {element.page_number}")
        print(f"    Preview: {element.text[:60]}...")

    # Case-sensitive search
    case_sensitive_results = document.search_content("Document", case_sensitive=True)
    print(
        f"\n✓ Case-sensitive search for 'Document': {len(case_sensitive_results)} matches"
    )

    # Search including tables
    table_search = document.search_content("Price", include_tables=True)
    print(f"\n✓ Search for 'Price' (including tables): {len(table_search)} matches")

    # Get content by page
    page_1_content = document.get_content_by_page(1, format_type="text")
    page_2_content = document.get_content_by_page(2, format_type="markdown")
    print(f"\n✓ Page content extraction:")
    print(f"  Page 1 content length: {len(page_1_content)} chars")
    print(f"  Page 2 content length: {len(page_2_content)} chars")


# ============================================================================
# 5. CONTENT CHUNKING (for Vector DBs)
# ============================================================================


def demonstrate_chunking(document):
    """Demonstrate content chunking for vector databases"""
    print("\n5. CONTENT CHUNKING (for Vector DBs)")
    print("-" * 36)

    # Basic text chunking
    text_chunks = document.get_text_chunks(target_size=200, tolerance=0.2)
    print(f"✓ Text chunks (target 200 chars): {len(text_chunks)} chunks")

    for i, chunk in enumerate(text_chunks):
        print(f"  Chunk {i+1}: {len(chunk)} chars - {chunk[:50]}...")

    # Markdown chunking
    markdown_chunks = document.get_markdown_chunks(target_size=250, tolerance=0.15)
    print(f"\n✓ Markdown chunks (target 250 chars): {len(markdown_chunks)} chunks")

    # Element-based chunking with metadata
    chunked_elements = document.get_chunked_elements(
        target_size=300, tolerance=0.1, format_type="text"
    )
    print(f"\n✓ Element-based chunks: {len(chunked_elements)} chunks")

    if chunked_elements:
        chunk = chunked_elements[0]
        print(f"  Sample chunk metadata:")
        print(f"    Content length: {len(chunk['content'])}")
        print(f"    Element type: {chunk['element_type']}")
        print(f"    Page number: {chunk['page_number']}")
        print(f"    Chunk index: {chunk['chunk_index']}")

    # Utility chunking functions
    standalone_text = (
        "This is a long text that we want to chunk into smaller pieces for processing."
    )
    standalone_chunks = chunk_text(standalone_text, target_size=30)
    print(f"\n✓ Standalone text chunking: {len(standalone_chunks)} chunks")

    markdown_text = "# Header\n\nThis is some markdown content with **bold** text.\n\n## Subheader\n\nMore content here."
    markdown_standalone_chunks = chunk_markdown(markdown_text, target_size=40)
    print(f"✓ Standalone markdown chunking: {len(markdown_standalone_chunks)} chunks")


# ============================================================================
# 6. EXPORT FORMATS
# ============================================================================


def demonstrate_export_formats(document):
    """Demonstrate various export format capabilities"""
    print("\n6. EXPORT FORMATS")
    print("-" * 17)

    # Convert to dictionary
    doc_dict = document.to_dict()
    print(f"✓ Dictionary format:")
    print(f"  Keys: {list(doc_dict.keys())}")
    print(f"  Metadata keys: {list(doc_dict['metadata'].keys())}")

    # Convert to markdown
    markdown_doc = document.to_markdown()
    print(f"\n✓ Markdown format: {len(markdown_doc)} characters")
    print(f"  Preview: {markdown_doc[:100]}...")

    # Convert to HTML
    html_doc = document.to_html()
    print(f"\n✓ HTML format: {len(html_doc)} characters")
    print(f"  Contains HTML tags: {'<html>' in html_doc}")

    # Try pandas conversion (if available)
    try:
        pandas_tables = document.to_pandas_tables()
        print(f"\n✓ Pandas tables: {len(pandas_tables)} DataFrames")
        for i, df in enumerate(pandas_tables):
            print(f"  Table {i+1}: {df.shape} shape")
    except ImportError:
        print(f"\n⚠ Pandas not available for table conversion")


# ============================================================================
# 7. DOCUMENT ANALYSIS
# ============================================================================


def demonstrate_document_analysis(document):
    """Demonstrate document analysis and statistics"""
    print("\n7. DOCUMENT ANALYSIS")
    print("-" * 20)

    # Get comprehensive statistics
    stats = document.get_statistics()
    print(f"✓ Document statistics:")
    print(f"  Content length: {stats['content_length']} chars")
    print(f"  Word count: {stats['word_count']} words")
    print(f"  Average words per element: {stats['average_words_per_element']:.1f}")
    print(f"  Element types: {stats['element_types']}")

    # Reading time estimation
    reading_time = document.get_reading_time()
    print(f"\n✓ Reading time estimation:")
    print(f"  Estimated time: {reading_time['minutes']}m {reading_time['seconds']}s")
    print(f"  Word count: {reading_time['word_count']} words")
    print(f"  Reading speed: {reading_time['words_per_minute']} WPM")

    # Language analysis
    language_info = document.get_language_info()
    print(f"\n✓ Language analysis:")
    print(f"  Detected language: {language_info['language']}")
    print(f"  Confidence: {language_info['confidence']:.2f}")
    print(f"  Total characters: {language_info['total_characters']}")

    # Extract key phrases
    key_phrases = document.extract_key_phrases(max_phrases=5)
    print(f"\n✓ Key phrases:")
    for phrase, count in key_phrases:
        print(f"  '{phrase}': {count} occurrences")

    # Validate document structure
    validation_errors = document.validate()
    print(f"\n✓ Document validation:")
    if validation_errors:
        print(f"  Errors found: {len(validation_errors)}")
        for error in validation_errors[:3]:  # Show first 3 errors
            print(f"    - {error}")
    else:
        print(f"  ✓ Document structure is valid")


# ============================================================================
# 8. BATCH OPERATIONS
# ============================================================================


def create_sample_batch():
    """Create a sample document batch for demonstration"""
    # Create multiple sample documents
    doc1_data = create_sample_api_response()
    doc1 = Document.from_api_response(doc1_data, "sample_document.pdf")

    # Create a second document with different content
    doc2_data = [
        {
            "id": "elem_004",
            "element_type": "paragraph",
            "content": {
                "html": "<p>This is the introduction to our second document about financial analysis.</p>",
                "markdown": "This is the introduction to our second document about financial analysis.",
                "text": "This is the introduction to our second document about financial analysis.",
            },
            "source": {
                "file": {
                    "extension": "docx",
                    "id": "file_456",
                    "index": 0,
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "original_mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "name": "financial_report.docx",
                },
                "page": {"page_number": 1, "index": 0},
                "element": {"characters": 78, "words": 13, "sentences": 1},
            },
        }
    ]
    doc2 = Document.from_api_response(doc2_data, "financial_report.docx")

    return DocumentBatch([doc1, doc2])


def demonstrate_batch_operations():
    """Demonstrate batch operations with multiple documents"""
    print("\n8. BATCH OPERATIONS")
    print("-" * 19)

    # Create a batch of documents
    batch = create_sample_batch()
    print(f"✓ Document batch created with {len(batch)} documents")

    # Batch properties
    print(f"  Filenames: {batch.filenames}")
    print(f"  File types: {batch.file_types}")
    print(f"  Total pages: {batch.total_pages}")
    print(f"  Total content length: {batch.total_content_length}")
    print(f"  Total tables: {batch.total_tables}")

    # Search across all documents
    search_results = batch.search_all("document")
    print(
        f"\n✓ Cross-document search for 'document': {len(search_results)} documents matched"
    )
    for doc, matches in search_results:
        print(f"  {doc.filename}: {len(matches)} matches")

    # Filter batch by file type
    pdf_batch = batch.filter_by_type("pdf")
    docx_batch = batch.filter_by_type("docx")
    print(f"\n✓ Filtering by file type:")
    print(f"  PDF documents: {len(pdf_batch)}")
    print(f"  DOCX documents: {len(docx_batch)}")

    # Get all chunks from batch
    all_chunks = batch.get_all_text_chunks(target_size=150, include_metadata=True)
    print(f"\n✓ Batch chunking: {len(all_chunks)} chunks")
    if all_chunks:
        chunk = all_chunks[0]
        print(f"  Sample chunk metadata: {list(chunk['metadata'].keys())}")

    # Get combined content
    combined_text = batch.to_combined_text()
    combined_markdown = batch.to_combined_markdown()
    print(f"\n✓ Combined formats:")
    print(f"  Combined text: {len(combined_text)} chars")
    print(f"  Combined markdown: {len(combined_markdown)} chars")

    # Batch statistics
    batch_stats = batch.get_statistics()
    print(f"\n✓ Batch statistics:")
    print(f"  Document count: {batch_stats['document_count']}")
    print(
        f"  Average content length: {batch_stats['content_length_distribution']['average']:.0f}"
    )
    print(
        f"  Average pages per doc: {batch_stats['average_metrics']['pages_per_document']:.1f}"
    )

    return batch


# ============================================================================
# 9. ADVANCED FEATURES
# ============================================================================


def demonstrate_advanced_features(batch):
    """Demonstrate advanced features and analysis"""
    print("\n9. ADVANCED FEATURES")
    print("-" * 20)

    # Find documents with specific keywords
    keyword_results = batch.find_documents_with_keyword("document")
    print(f"✓ Keyword analysis for 'document':")
    for doc, count in keyword_results:
        print(f"  {doc.filename}: {count} occurrences")

    # Content similarity analysis
    similarity_matrix = batch.get_content_similarity_matrix()
    print(f"\n✓ Content similarity matrix:")
    print(f"  Matrix size: {len(similarity_matrix)}x{len(similarity_matrix[0])}")
    if len(similarity_matrix) >= 2:
        similarity = similarity_matrix[0][1]
        print(f"  Similarity between docs 1&2: {similarity:.3f}")

    # Get batch summary
    summary = batch.get_summary(max_chars_per_doc=100)
    print(f"\n✓ Batch summary:")
    print(f"  Summary length: {len(summary)} chars")
    print(f"  Preview: {summary[:150]}...")

    # Validate batch structure
    batch_errors = batch.validate()
    print(f"\n✓ Batch validation:")
    if batch_errors:
        print(f"  Errors found: {len(batch_errors)}")
        for error in batch_errors[:3]:
            print(f"    - {error}")
    else:
        print(f"  ✓ Batch structure is valid")

    # Filter documents by element type
    docs_with_tables = batch.get_documents_by_element_type("table")
    docs_with_paragraphs = batch.get_documents_by_element_type("paragraph")
    print(f"\n✓ Filter by element type:")
    print(f"  Documents with tables: {len(docs_with_tables)}")
    print(f"  Documents with paragraphs: {len(docs_with_paragraphs)}")


# ============================================================================
# 10. FILE OPERATIONS & PERSISTENCE
# ============================================================================


def demonstrate_file_operations(batch):
    """Demonstrate file operations and persistence"""
    print("\n10. FILE OPERATIONS & PERSISTENCE")
    print("-" * 34)

    # Save batch to JSON (demonstrate but don't actually save)
    batch_dict = batch.to_dict()
    print(f"✓ JSON export preparation:")
    print(f"  Batch dict keys: {list(batch_dict.keys())}")
    print(f"  Metadata keys: {list(batch_dict['metadata'].keys())}")
    print(f"  Serializable structure ready for JSON export")

    # Demonstrate CSV export capability for tables
    print(f"\n✓ Table export capabilities:")
    all_tables = batch.get_all_tables()
    print(f"  Total tables across all documents: {len(all_tables)}")

    if all_tables:
        doc, table = all_tables[0]
        csv_content = table.to_csv_string()
        print(f"  Sample CSV export (first table):")
        print(f"    Filename: {doc.filename}")
        print(f"    CSV length: {len(csv_content)} chars")
        print(f"    CSV preview: {csv_content[:80]}...")

    print(f"\n✓ File operation methods available:")
    print(f"  - batch.save_to_json(filepath)")
    print(f"  - batch.export_tables_to_csv(output_dir)")
    print(f"  - DocumentBatch.load_from_json(filepath)")
    print(f"  - Document.from_api_response(response_data)")


# ============================================================================
# 11. ERROR HANDLING & EDGE CASES
# ============================================================================


def demonstrate_error_handling():
    """Demonstrate error handling and edge cases"""
    print("\n11. ERROR HANDLING & EDGE CASES")
    print("-" * 32)

    # Handle empty API response
    empty_response = []
    empty_doc = Document.from_api_response(empty_response, "empty_document.pdf")
    print(f"✓ Empty response handling:")
    print(f"  Document created: {empty_doc.filename}")
    print(f"  Content length: {len(empty_doc.content)}")
    print(f"  Elements: {len(empty_doc.elements)}")

    # Handle malformed data gracefully
    malformed_response = [{"invalid": "data"}]
    try:
        malformed_doc = Document.from_api_response(malformed_response, "malformed.pdf")
        print(f"\n✓ Malformed data handling:")
        print(f"  Document created successfully: {malformed_doc.filename}")
        print(f"  Graceful degradation applied")
    except Exception as e:
        print(f"\n⚠ Error handling malformed data: {str(e)}")

    # Handle missing optional dependencies
    print(f"\n✓ Optional dependency handling:")
    try:
        # This will work regardless of pandas availability
        doc = Document.from_api_response(create_sample_api_response())
        chunks = doc.get_text_chunks()
        print(f"  Core functionality works: {len(chunks)} chunks created")
    except Exception as e:
        print(f"  Core functionality error: {str(e)}")

    # Validate document with errors
    invalid_elements = [
        DocumentElement(
            content=ElementContent(text="test"),
            element_type="",  # Missing element type
            id="",  # Missing ID
            source=None,  # Invalid source
        )
    ]

    try:
        invalid_doc = Document(
            content="Test content",
            metadata=DocumentMetadata(filename="test.pdf"),
            elements=invalid_elements,
        )
        validation_errors = invalid_doc.validate()
        print(f"\n✓ Validation error detection:")
        print(f"  Errors found: {len(validation_errors)}")
        for error in validation_errors[:3]:
            print(f"    - {error}")
    except Exception as e:
        print(f"\n⚠ Validation error: {str(e)}")


# ============================================================================
# 12. PRACTICAL USAGE PATTERNS
# ============================================================================


def demonstrate_usage_patterns():
    """Demonstrate common usage patterns"""
    print("\n12. PRACTICAL USAGE PATTERNS")
    print("-" * 29)

    print("✓ Common usage patterns:")
    print(
        """
    # Basic document processing
    document = Document.from_api_response(api_response)
    content = document.content
    tables = document.tables
    
    # Search and filter
    results = document.search_content("keyword")
    page_content = document.get_content_by_page(1)
    table_elements = document.get_elements_by_type("table")
    
    # Chunking for vector databases
    chunks = document.get_text_chunks(target_size=500)
    chunked_elements = document.get_chunked_elements(
        target_size=400, 
        format_type="markdown"
    )
    
    # Batch processing
    batch = DocumentBatch([doc1, doc2, doc3])
    all_chunks = batch.get_all_text_chunks(include_metadata=True)
    combined_content = batch.to_combined_markdown()
    
    # Export and persistence
    batch.save_to_json("documents.json")
    batch.export_tables_to_csv("./tables/")
    loaded_batch = DocumentBatch.load_from_json("documents.json")
    """
    )


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Main function to run all demonstrations"""
    try:
        # Run all demonstrations
        document = demonstrate_basic_operations()
        demonstrate_document_elements(document)
        demonstrate_table_operations(document)
        demonstrate_search_and_filtering(document)
        demonstrate_chunking(document)
        demonstrate_export_formats(document)
        demonstrate_document_analysis(document)

        batch = demonstrate_batch_operations()
        demonstrate_advanced_features(batch)
        demonstrate_file_operations(batch)
        demonstrate_error_handling()
        demonstrate_usage_patterns()

        print("\n" + "=" * 60)
        print("✓ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nThe Cerevox Document Loader provides comprehensive functionality for:")
        print("- Document parsing and element extraction")
        print("- Table extraction and pandas integration")
        print("- Content search and filtering")
        print("- Vector database preparation (chunking)")
        print("- Multiple export formats")
        print("- Batch processing capabilities")
        print("- Advanced analysis and statistics")
        print("- Robust error handling")
        print("\nRefer to the individual function examples above for detailed usage.")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {str(e)}")
        print("Please check your environment and dependencies.")


if __name__ == "__main__":
    main()
