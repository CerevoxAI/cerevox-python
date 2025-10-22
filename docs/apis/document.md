# Document API Reference

> **📌 Note:** This reference currently covers the Lexa document processing API. For the new Hippo (RAG) and Account management APIs introduced in v0.2.0, please refer to:
> - **Hippo RAG API**: See [`examples/account_hippo_usage.py`](../examples/account_hippo_usage.py) and inline docstrings in `cerevox.apis.Hippo` / `cerevox.apis.AsyncHippo`
> - **Account API**: See [`examples/account_hippo_usage.py`](../examples/account_hippo_usage.py) and inline docstrings in `cerevox.apis.Account` / `cerevox.apis.AsyncAccount`
> - Comprehensive API reference for these new APIs will be added in a future update

## Overview

**Flagship Results @ Mini Cost** - Cerevox delivers 99.5% accuracy at 80% lower cost with precision retrieval that provides 70% smaller, more relevant context.

Cerevox provides three powerful APIs:
- **Lexa** - Document parsing with SOTA accuracy (documented below)
- **Hippo** - RAG operations with precision retrieval, semantic search and Q&A (see examples and docstrings)
- **Account** - Enterprise user management and authentication (see examples and docstrings)

## Table of Contents

- [DocumentBatch](#documentbatch)
  - [Properties](#properties)
  - [Accessing Documents](#accessing-documents)
  - [Methods](#methods-2)
    - [search_all(query, include_metadata=False)](#search_allquery-include_metadatafalse)
    - [filter_by_type(file_type)](#filter_by_typefile_type)
    - [get_all_text_chunks(**options)](#get_all_text_chunksoptions)
    - [get_all_markdown_chunks(**options)](#get_all_markdown_chunksoptions)
    - [save_to_json(filepath)](#save_to_jsonfilepath)
    - [to_combined_text()](#to_combined_text)
    - [to_combined_markdown()](#to_combined_markdown)
    - [get_all_tables()](#get_all_tables)
    - [to_pandas_tables()](#to_pandas_tables)
    - [export_tables_to_csv(directory)](#export_tables_to_csvdirectory)
- [Document](#document)
  - [Properties](#properties-1)
  - [Methods](#methods-3)
    - [to_markdown()](#to_markdown)
    - [to_html()](#to_html)
    - [to_dict()](#to_dict)
    - [search_content(query, include_metadata=False)](#search_contentquery-include_metadatafalse)
    - [get_elements_by_page(page_number)](#get_elements_by_pagepage_number)
    - [get_elements_by_type(element_type)](#get_elements_by_typeelement_type)
    - [get_statistics()](#get_statistics)
- [Standalone Functions](#standalone-functions)
  - [chunk_text(text, target_size, tolerance)](#chunk_texttext-target_size-tolerance)
  - [chunk_markdown(markdown, target_size, tolerance, preserve_tables)](#chunk_markdownmarkdown-target_size-tolerance-preserve_tables)

---

## DocumentBatch

Collection of documents with batch operations. This is the primary return type from AsyncLexa and Lexa parsing methods.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `documents` | List[Document] | Collection of individual Document objects |
| `total_pages` | int | Total pages across all documents |
| `count` | int | Number of documents in the batch |
| `file_types` | List[str] | Unique file types present in the batch |
| `total_size_bytes` | int | Total size of all documents in bytes |

### Accessing Documents

```python
# Access individual documents
first_doc = documents[0]  # Get first document
doc_by_name = documents["filename.pdf"]  # Get document by filename

# Iterate through documents
for doc in documents:
    print(f"Processing {doc.filename}")

# Get specific document
doc = documents.get_document("filename.pdf")
```

### Methods

#### search_all(query, include_metadata=False)

Search across all documents in the batch using text-based queries.

```python
# Simple text search
results = documents.search_all("revenue growth")

# Search with metadata
results = documents.search_all(
    "financial projections", 
    include_metadata=True
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | str | Yes | - | Plain text search query string |
| `include_metadata` | bool | No | False | Include metadata in results |

**Returns:** `List[dict]` - Search results across all documents

#### filter_by_type(file_type)

Filter documents by file type.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_type` | str | Yes | File type ('pdf', 'docx', 'html', etc.) |

**Returns:** `List[Document]` - Filtered documents

#### get_all_text_chunks(**options)

Get optimized text chunks for vector databases.

```python
chunks = documents.get_all_text_chunks(
    target_size=500,
    tolerance=0.1,
    include_metadata=True
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target_size` | int | No | 500 | Target size for each chunk in characters |
| `tolerance` | float | No | 0.1 | Size tolerance as percentage (0.0-1.0) |
| `include_metadata` | bool | No | True | Include document metadata with chunks |

**Returns:** `List[dict]` - Optimized text chunks with metadata

#### get_all_markdown_chunks(**options)

Get optimized markdown chunks for vector databases.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target_size` | int | No | 800 | Target size for each chunk in characters |
| `tolerance` | float | No | 0.1 | Size tolerance as percentage |
| `include_metadata` | bool | No | True | Include metadata |
| `preserve_tables` | bool | No | True | Keep table structures intact |

**Returns:** `List[dict]` - Optimized markdown chunks

#### save_to_json(filepath)

Save batch to JSON file.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filepath` | str | Yes | Path to save JSON file |

#### to_combined_text()

**Returns:** `str` - All document content as single text string

#### to_combined_markdown()

**Returns:** `str` - All document content as single markdown string

#### get_all_tables()

**Returns:** `List[dict]` - All tables from all documents

#### to_pandas_tables()

**Returns:** `dict` - All tables as pandas DataFrames, organized by filename

#### export_tables_to_csv(directory)

Export all tables to CSV files.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `directory` | str | Yes | Directory path for CSV files |

---

## Document

Individual document with rich metadata and content access.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `filename` | str | Original filename of the document |
| `file_type` | str | Document type (e.g., 'pdf', 'docx', 'html') |
| `page_count` | int | Number of pages in the document |
| `content` | str | Plain text content of the document |
| `elements` | List[dict] | Structured document elements with metadata |
| `tables` | List[dict] | Extracted tables from the document |

### Methods

#### to_markdown()

Convert document to formatted markdown.

**Returns:** `str` - Markdown formatted content

#### to_html()

Convert document to HTML format.

**Returns:** `str` - HTML formatted content

#### to_dict()

Convert document to dictionary format.

**Returns:** `dict` - Document as dictionary

#### search_content(query, include_metadata=False)

Search for content within the document.

```python
matches = doc.search_content("revenue", include_metadata=True)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | str | Yes | - | Search query string |
| `include_metadata` | bool | No | False | Include metadata in results |

**Returns:** `List[dict]` - Search results with optional metadata

#### get_elements_by_page(page_number)

Get all elements from a specific page.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_number` | int | Yes | Page number (1-based) |

**Returns:** `List[dict]` - Elements from the specified page

#### get_elements_by_type(element_type)

Filter elements by type.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `element_type` | str | Yes | Element type ('table', 'paragraph', 'header', etc.) |

**Returns:** `List[dict]` - Filtered elements

#### get_statistics()

Get document statistics.

**Returns:** `dict` - Statistics including character count, word count, sentences

---

## Standalone Functions

*Note: These functions operate independently and do not require an API key.*

### chunk_text(text, target_size, tolerance)

Chunk plain text content for vector databases.

```python
from cerevox import chunk_text

chunks = chunk_text(text_content, target_size=500, tolerance=0.1)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | str | Yes | - | Text content to chunk |
| `target_size` | int | No | 500 | Target chunk size in characters |
| `tolerance` | float | No | 0.1 | Size tolerance percentage |

**Returns:** `List[dict]` - Text chunks with metadata

### chunk_markdown(markdown, target_size, tolerance, preserve_tables)

Chunk markdown content while preserving structure.

```python
from cerevox import chunk_markdown

chunks = chunk_markdown(
    markdown_content, 
    target_size=800, 
    preserve_tables=True
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `markdown` | str | Yes | - | Markdown content to chunk |
| `target_size` | int | No | 800 | Target chunk size in characters |
| `tolerance` | float | No | 0.1 | Size tolerance percentage |
| `preserve_tables` | bool | No | True | Keep table structures intact |

**Returns:** `List[dict]` - Markdown chunks with preserved structure
