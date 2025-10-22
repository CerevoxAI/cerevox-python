# Advanced Examples

Advanced usage patterns and real-world applications with Cerevox. Leverage **Flagship Results @ Mini Cost** with precision retrieval that delivers 70% smaller context, enabling 80% cost reduction and 10x more requests while maintaining 99.5% accuracy.

## Table of Contents

- [Content Analysis & Search](#content-analysis--search)
  - [Document Statistics and Analysis](#document-statistics-and-analysis)
  - [Advanced Content Search](#advanced-content-search)
  - [Batch Document Analysis](#batch-document-analysis)
- [Table Extraction & Processing](#table-extraction--processing)
  - [Advanced Table Analysis](#advanced-table-analysis)
  - [Convert to Pandas for Analysis](#convert-to-pandas-for-analysis)
  - [Export Tables](#export-tables)
- [Performance Optimization](#performance-optimization)
  - [High-Volume Processing](#high-volume-processing)
  - [Progress Tracking](#progress-tracking)
- [Document Format Conversion](#document-format-conversion)
  - [Multiple Output Formats](#multiple-output-formats)
- [Advanced Element Processing](#advanced-element-processing)
  - [Element Type Filtering](#element-type-filtering)
  - [Structured Data Extraction](#structured-data-extraction)
  - [Cross-Document Element Analysis](#cross-document-element-analysis)
- [Error Handling & Resilience](#error-handling--resilience)
  - [Robust Processing Pipeline](#robust-processing-pipeline)
  - [Custom Error Recovery](#custom-error-recovery)
  - [Monitoring and Logging](#monitoring-and-logging)
- [Custom Integration Patterns](#custom-integration-patterns)
  - [Database Integration](#database-integration)
  - [API Integration](#api-integration)
  - [Custom Processing Pipeline](#custom-processing-pipeline)

---

## Content Analysis & Search

### Document Statistics and Analysis

```python
from cerevox import AsyncLexa

async with AsyncLexa() as client:
    documents = await client.parse(["financial_report.pdf"])
    doc = documents[0]
    
    # Get comprehensive statistics
    stats = doc.get_statistics()
    print(f"Document Analysis:")
    print(f"  Characters: {stats['characters']:,}")
    print(f"  Words: {stats['words']:,}")
    print(f"  Sentences: {stats['sentences']:,}")
    print(f"  Pages: {doc.page_count}")
    print(f"  Tables: {len(doc.tables)}")
```

### Advanced Content Search

```python
# Search with metadata for context
matches = doc.search_content("revenue growth", include_metadata=True)

for match in matches:
    print(f"Found on page {match['page_number']}:")
    print(f"  Context: {match['context']}")
    print(f"  Element type: {match['element_type']}")
    print(f"  Confidence: {match.get('confidence', 'N/A')}")
```

### Batch Document Analysis

```python
# Analyze multiple documents together
documents = await client.parse([
    "q1_report.pdf",
    "q2_report.pdf", 
    "q3_report.pdf",
    "q4_report.pdf"
])

# Cross-document search
all_matches = documents.search_all("market share", include_metadata=True)

# Content similarity analysis
similarity_matrix = documents.get_content_similarity_matrix()
print("Document similarity matrix:", similarity_matrix)

# Extract key phrases across all documents
key_phrases = documents.extract_key_phrases(top_n=20)
print("Key phrases:", key_phrases)
```

## Table Extraction & Processing

### Advanced Table Analysis

```python
# Extract and analyze all tables
all_tables = documents.get_all_tables()
print(f"Found {len(all_tables)} tables across {len(documents)} documents")

for table in all_tables:
    print(f"Table from {table['document_filename']}:")
    print(f"  Headers: {table['headers']}")
    print(f"  Rows: {len(table['rows'])}")
    print(f"  Columns: {len(table['headers'])}")
```

### Convert to Pandas for Analysis

```python
import pandas as pd

# Convert all tables to pandas DataFrames
df_tables = documents.to_pandas_tables()

for filename, tables in df_tables.items():
    print(f"📄 {filename}: {len(tables)} tables")
    
    for i, table in enumerate(tables):
        print(f"  Table {i+1} shape: {table.shape}")
        
        # Perform analysis
        if 'Revenue' in table.columns:
            total_revenue = table['Revenue'].sum()
            print(f"    Total Revenue: ${total_revenue:,.2f}")
```

### Export Tables

```python
# Export all tables to CSV files
documents.export_tables_to_csv("./exported_tables/")

# Or work with individual tables
for i, table in enumerate(all_tables):
    df = pd.DataFrame(table['rows'], columns=table['headers'])
    df.to_csv(f"table_{i}.csv", index=False)
```

## Performance Optimization

### High-Volume Processing

```python
import asyncio
from pathlib import Path

async def process_large_document_set():
    # Configure for high-performance processing
    async with AsyncLexa(
        api_key="your-api-key",
        max_concurrent=20,      # Increase parallel processing
        timeout=120.0,          # Extended timeout for large files
        max_retries=5           # Enhanced error resilience
    ) as client:
        
        # Get all documents in directory
        doc_files = [str(p) for p in Path("./documents").glob("**/*") 
                    if p.suffix.lower() in ['.pdf', '.docx', '.pptx', '.html']]
        
        print(f"Processing {len(doc_files)} documents...")
        
        # Process in batches to manage memory
        batch_size = 50
        all_chunks = []
        
        for i in range(0, len(doc_files), batch_size):
            batch = doc_files[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}...")
            
            # Parse batch
            documents = await client.parse(
                files=batch,
                progress_callback=lambda status: print(f"Status: {status}")
            )
            
            # Get chunks immediately to free memory
            chunks = documents.get_all_text_chunks(target_size=500)
            all_chunks.extend(chunks)
            
            print(f"Batch complete. Total chunks so far: {len(all_chunks)}")
        
        return all_chunks

# Run the processing
chunks = await process_large_document_set()
```

### Progress Tracking

```python
class ProgressTracker:
    def __init__(self, total_files):
        self.total_files = total_files
        self.completed = 0
        
    def callback(self, status):
        if status.status == "completed":
            self.completed += 1
            progress = (self.completed / self.total_files) * 100
            print(f"Progress: {progress:.1f}% ({self.completed}/{self.total_files})")

# Use with processing
async def process_with_progress():
    files = ["doc1.pdf", "doc2.docx", "doc3.pptx"]
    tracker = ProgressTracker(len(files))
    
    async with AsyncLexa() as client:
        documents = await client.parse(
            files=files,
            progress_callback=tracker.callback
        )
    
    return documents
```

## Document Format Conversion

### Multiple Output Formats

```python
async with AsyncLexa() as client:
    documents = await client.parse(["presentation.pptx"])
    doc = documents[0]
    
    # Convert to different formats
    markdown = doc.to_markdown()
    html = doc.to_html()
    plain_text = doc.content
    structured_data = doc.to_dict()
    
    # Save to files
    with open("output.md", "w") as f:
        f.write(markdown)
    
    with open("output.html", "w") as f:
        f.write(html)
    
    with open("output.txt", "w") as f:
        f.write(plain_text)
    
    # Save structured data
    import json
    with open("output.json", "w") as f:
        json.dump(structured_data, f, indent=2)
```

### Batch Format Conversion

```python
# Convert all documents to markdown
combined_markdown = documents.to_combined_markdown()
with open("all_documents.md", "w") as f:
    f.write(combined_markdown)

# Convert to HTML
combined_html = documents.to_combined_html()
with open("all_documents.html", "w") as f:
    f.write(combined_html)

# Save batch as JSON
documents.save_to_json("documents_batch.json")
```

## Advanced Element Processing

### Filter by Element Type

```python
doc = documents[0]

# Get specific types of elements
headers = doc.get_elements_by_type("header")
paragraphs = doc.get_elements_by_type("paragraph")
tables = doc.get_elements_by_type("table")
images = doc.get_elements_by_type("image")

print(f"Document structure:")
print(f"  Headers: {len(headers)}")
print(f"  Paragraphs: {len(paragraphs)}")
print(f"  Tables: {len(tables)}")
print(f"  Images: {len(images)}")
```

### Page-by-Page Processing

```python
# Process each page individually
for page_num in range(1, doc.page_count + 1):
    page_elements = doc.get_elements_by_page(page_num)
    
    print(f"Page {page_num}:")
    for element in page_elements:
        print(f"  {element['type']}: {element['content'][:100]}...")
```

### Custom Element Processing

```python
def extract_financial_data(documents):
    """Extract financial figures from documents"""
    import re
    
    financial_data = []
    currency_pattern = r'\$[\d,]+\.?\d*'
    
    for doc in documents:
        amounts = re.findall(currency_pattern, doc.content)
        financial_data.extend([{
            'document': doc.filename,
            'amount': amount,
            'context': 'extracted from content'
        } for amount in amounts])
    
    return financial_data

# Extract financial data
financial_figures = extract_financial_data(documents)
print(f"Found {len(financial_figures)} financial figures")
```

## Error Handling & Resilience

### Comprehensive Error Handling

```python
from cerevox import (
    LexaError,
    LexaAuthError,
    LexaJobFailedError,
    LexaTimeoutError
)

async def robust_processing(files):
    results = []
    failed_files = []
    
    async with AsyncLexa() as client:
        for file_path in files:
            try:
                print(f"Processing {file_path}...")
                documents = await client.parse([file_path])
                results.extend(documents)
                print(f"✅ Successfully processed {file_path}")
                
            except LexaAuthError as e:
                print(f"❌ Authentication error: {e.message}")
                break  # Stop processing on auth errors
                
            except LexaJobFailedError as e:
                print(f"❌ Failed to process {file_path}: {e.message}")
                failed_files.append(file_path)
                
            except LexaTimeoutError as e:
                print(f"⏰ Timeout processing {file_path}: {e.message}")
                failed_files.append(file_path)
                
            except LexaError as e:
                print(f"❌ Error processing {file_path}: {e.message}")
                failed_files.append(file_path)
    
    return results, failed_files

# Process with error handling
successful_docs, failed_files = await robust_processing(file_list)
print(f"Processed {len(successful_docs)} documents successfully")
print(f"Failed to process {len(failed_files)} files")
```

### Retry Logic

```python
import asyncio
from random import uniform

async def process_with_retries(files, max_retries=3):
    """Process files with exponential backoff retry logic"""
    
    async def process_single_file(file_path, attempt=1):
        try:
            async with AsyncLexa() as client:
                return await client.parse([file_path])
        except (LexaTimeoutError, LexaJobFailedError) as e:
            if attempt < max_retries:
                # Exponential backoff with jitter
                delay = 2 ** attempt + uniform(0, 1)
                print(f"Retrying {file_path} in {delay:.1f}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)
                return await process_single_file(file_path, attempt + 1)
            else:
                raise e
    
    results = []
    for file_path in files:
        try:
            docs = await process_single_file(file_path)
            results.extend(docs)
        except Exception as e:
            print(f"Final failure for {file_path}: {e}")
    
    return results
```

## Custom Integration Patterns

### Database Integration

```python
import sqlite3
import json

async def process_and_store_in_db(files, db_path="documents.db"):
    """Process documents and store in SQLite database"""
    
    # Create database schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            content TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Process documents
    async with AsyncLexa() as client:
        documents = await client.parse(files)
        
        for doc in documents:
            cursor.execute('''
                INSERT INTO documents (filename, content, metadata)
                VALUES (?, ?, ?)
            ''', (
                doc.filename,
                doc.content,
                json.dumps(doc.to_dict())
            ))
    
    conn.commit()
    conn.close()
    print(f"Stored {len(documents)} documents in database")

# Usage
await process_and_store_in_db(["doc1.pdf", "doc2.docx"])
```

### API Integration

```python
import httpx

async def process_and_send_to_api(files, api_endpoint):
    """Process documents and send results to external API"""
    
    async with AsyncLexa() as client:
        documents = await client.parse(files)
        chunks = documents.get_all_text_chunks(target_size=500)
    
    # Send to external API
    async with httpx.AsyncClient() as http_client:
        for chunk in chunks:
            payload = {
                "content": chunk["content"],
                "metadata": chunk,
                "source": "cerevox"
            }
            
            response = await http_client.post(api_endpoint, json=payload)
            if response.status_code == 200:
                print(f"✅ Sent chunk from {chunk['document_filename']}")
            else:
                print(f"❌ Failed to send chunk: {response.status_code}")

# Usage
await process_and_send_to_api(files, "https://api.example.com/documents")
``` 