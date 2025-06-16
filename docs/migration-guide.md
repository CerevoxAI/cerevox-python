# Migration Guide

Migrate from popular document processing tools to Cerevox for better performance and accuracy.

## Table of Contents

- [Performance Comparison](#performance-comparison)
- [From LlamaIndex](#from-llamaindex)
- [From Unstructured](#from-unstructured)
- [From Amazon Textract](#from-amazon-textract)
- [From PyPDF2/pdfplumber](#from-pypdf2pdfplumber)
- [From DocumentCloud](#from-documentcloud)
- [Migration Checklist](#migration-checklist)
  - [✅ Pre-Migration](#-pre-migration)
  - [✅ During Migration](#-during-migration)
  - [✅ Post-Migration](#-post-migration)
- [Common Migration Patterns](#common-migration-patterns)
  - [Pattern 1: Basic Text Extraction](#pattern-1-basic-text-extraction)
  - [Pattern 2: Batch Processing](#pattern-2-batch-processing)
  - [Pattern 3: Vector Database Preparation](#pattern-3-vector-database-preparation)
- [Getting Help](#getting-help)

---

## Performance Comparison

| Tool | Processing Speed | Table Accuracy | Async Support | Vector DB Ready |
|------|-----------------|----------------|---------------|-----------------|
| **Cerevox** | ⚡ Fastest | 🎯 Highest | ✅ Native | ✅ Optimized |
| LlamaIndex | 🐌 Slow | ⚠️ Basic | ❌ No | ⚠️ Manual |
| Unstructured | 🐌 Slow | ⚠️ Medium | ❌ No | ⚠️ Manual |
| Textract | 🕐 Medium | ⚠️ Medium | ⚠️ Manual | ❌ No |
| PyPDF2 | 🕐 Medium | ❌ Poor | ❌ No | ❌ No |
| DocumentCloud | 🕐 Manual | ⚠️ Basic | ❌ Web Only | ❌ No |

---

## From LlamaIndex

LlamaIndex users can easily migrate to Cerevox for improved document parsing and chunking.

### Before (LlamaIndex)

```python
from llama_index import SimpleDirectoryReader, VectorStoreIndex
from llama_index.text_splitter import TokenTextSplitter

# Load documents
documents = SimpleDirectoryReader('docs').load_data()

# Split text
text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
nodes = text_splitter.get_nodes_from_documents(documents)

# Create index
index = VectorStoreIndex(nodes)
```

### After (Cerevox)

```python
from cerevox import AsyncLexa

# Better performance + async support + more accurate table extraction
async with AsyncLexa() as client:
    documents = await client.parse(glob.glob('docs/*'))
    
    # Get optimized chunks with rich metadata
    chunks = documents.get_all_text_chunks(
        target_size=500,
        include_metadata=True
    )
    
    # Ready for vector database or further processing
    for chunk in chunks:
        print(f"Document: {chunk['document_filename']}")
        print(f"Content: {chunk['content']}")
        print(f"Page: {chunk.get('page_number')}")
```

### Key Improvements

- **10x faster** document processing with async support
- **Better table extraction** with structure preservation  
- **Rich metadata** for enhanced retrieval
- **Native async** processing for better scalability

---

## From Unstructured

Unstructured users benefit from Cerevox's superior accuracy and async capabilities.

### Before (Unstructured)

```python
from unstructured.partition.auto import partition

# Process document
elements = partition(filename="document.pdf")

# Extract text
text_elements = [str(el) for el in elements if hasattr(el, 'text')]
```

### After (Cerevox)

```python
from cerevox import AsyncLexa

# More accurate + async + better structured output
async with AsyncLexa() as client:
    documents = await client.parse(["document.pdf"])
    doc = documents[0]
    
    # Get structured elements with rich metadata
    elements = doc.elements
    
    # Filter by element type
    headers = doc.get_elements_by_type("header")
    paragraphs = doc.get_elements_by_type("paragraph")
    tables = doc.get_elements_by_type("table")
    
    # Better table handling
    for table in doc.tables:
        print(f"Headers: {table['headers']}")
        print(f"Rows: {len(table['rows'])}")
```

### Key Improvements

- **Higher accuracy** especially for complex documents
- **Better table structure** preservation
- **Async processing** for handling multiple documents
- **Consistent metadata** across all element types

---

## From Amazon Textract

Amazon Textract users can migrate to Cerevox for simpler integration and better developer experience.

### Before (Amazon Textract)

```python
import boto3
import time

textract = boto3.client('textract')

# Start document analysis (async job)
response = textract.start_document_text_detection(
    DocumentLocation={'S3Object': {'Bucket': 'bucket', 'Name': 'document.pdf'}}
)
job_id = response['JobId']

# Poll for completion (manual polling required)
while True:
    response = textract.get_document_text_detection(JobId=job_id)
    status = response['JobStatus']
    
    if status == 'SUCCEEDED':
        # Extract text blocks
        blocks = response['Blocks']
        text = ' '.join([block['Text'] for block in blocks if block['BlockType'] == 'LINE'])
        break
    elif status == 'FAILED':
        raise Exception("Job failed")
    else:
        time.sleep(5)  # Wait and poll again
```

### After (Cerevox)

```python
from cerevox import AsyncLexa

# Automatic polling + better structured output + no AWS setup
async with AsyncLexa() as client:
    # Direct file processing - no manual polling needed
    documents = await client.parse(["document.pdf"])
    doc = documents[0]
    
    # Get text content
    text = doc.content
    
    # Get structured elements
    elements = doc.elements
    
    # Get tables with proper structure
    tables = doc.tables
    
    print(f"Processed {doc.page_count} pages")
    print(f"Found {len(tables)} tables")
```

### Key Improvements

- **No AWS setup** or credential management required
- **Automatic job polling** - no manual loops
- **Better structured output** with rich metadata
- **Superior table extraction** with preserved relationships

---

## From PyPDF2/pdfplumber

Users of basic PDF libraries can upgrade to Cerevox for AI-powered extraction.

### Before (PyPDF2)

```python
import PyPDF2

with open('document.pdf', 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    text = ''
    
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    # Basic text extraction only
    print(text)
```

### Before (pdfplumber)

```python
import pdfplumber

with pdfplumber.open('document.pdf') as pdf:
    text = ''
    tables = []
    
    for page in pdf.pages:
        text += page.extract_text()
        page_tables = page.extract_tables()
        tables.extend(page_tables)
```

### After (Cerevox)

```python
from cerevox import AsyncLexa

# AI-powered extraction with much better accuracy
async with AsyncLexa() as client:
    documents = await client.parse(["document.pdf"])
    doc = documents[0]
    
    # High-quality text extraction
    text = doc.content
    
    # Structured table extraction with headers
    tables = doc.tables
    for table in tables:
        print(f"Table headers: {table['headers']}")
        print(f"Rows: {len(table['rows'])}")
    
    # Rich metadata and element structure
    elements = doc.elements
    
    # Convert to different formats
    markdown = doc.to_markdown()
    html = doc.to_html()
```

### Key Improvements

- **AI-powered extraction** vs basic text parsing
- **Much better accuracy** for complex layouts
- **Proper table structure** with headers and relationships
- **Multiple output formats** (markdown, HTML, JSON)
- **Rich metadata** for each element

---

## From DocumentCloud

DocumentCloud users can migrate for better programmatic access and processing.

### Before (DocumentCloud)

```python
# Manual upload and processing through web interface
# Limited programmatic access
# Manual annotation and analysis
```

### After (Cerevox)

```python
from cerevox import AsyncLexa

# Full programmatic control with rich processing
async with AsyncLexa() as client:
    # Process multiple documents programmatically
    documents = await client.parse([
        "report1.pdf",
        "report2.docx", 
        "presentation.pptx"
    ])
    
    # Advanced search across all documents
    results = documents.search_all("budget allocation")
    
    # Export in multiple formats
    documents.save_to_json("processed_documents.json")
    
    # Get chunks ready for vector databases
    chunks = documents.get_all_text_chunks(target_size=500)
```

### Key Improvements

- **Full programmatic control** vs web interface dependency
- **Batch processing** of multiple documents
- **Advanced search** capabilities across document sets
- **Vector database preparation** for RAG applications

---

## Migration Checklist

### ✅ Pre-Migration

- [ ] Install Cerevox: `pip install cerevox`
- [ ] Get API key from [cerevox.ai/lexa](https://cerevox.ai/lexa)
- [ ] Review existing document processing pipeline
- [ ] Identify file types and volumes to process

### ✅ During Migration

- [ ] Update import statements to use Cerevox
- [ ] Replace synchronous calls with async/await pattern
- [ ] Update chunking logic to use Cerevox's optimized methods
- [ ] Test with a small subset of documents first
- [ ] Validate output format compatibility

### ✅ Post-Migration

- [ ] Monitor processing performance improvements
- [ ] Validate extraction accuracy improvements
- [ ] Update vector database integration if applicable
- [ ] Remove old dependencies and clean up code
- [ ] Update documentation and team training

## Common Migration Patterns

### Pattern 1: Basic Text Extraction

```python
# Old pattern (any tool)
def extract_text(file_path):
    # Tool-specific extraction logic
    return extracted_text

# New pattern (Cerevox)
async def extract_text(file_path):
    async with AsyncLexa() as client:
        documents = await client.parse([file_path])
        return documents[0].content
```

### Pattern 2: Batch Processing

```python
# Old pattern
def process_documents(file_paths):
    results = []
    for path in file_paths:
        result = process_single_file(path)  # Synchronous
        results.append(result)
    return results

# New pattern (Cerevox)
async def process_documents(file_paths):
    async with AsyncLexa() as client:
        documents = await client.parse(file_paths)  # Parallel processing
        return documents
```

### Pattern 3: Vector Database Preparation

```python
# Old pattern
def prepare_for_vector_db(documents):
    chunks = []
    for doc in documents:
        # Manual chunking logic
        doc_chunks = manual_chunk(doc.text, size=500)
        chunks.extend(doc_chunks)
    return chunks

# New pattern (Cerevox)
async def prepare_for_vector_db(file_paths):
    async with AsyncLexa() as client:
        documents = await client.parse(file_paths)
        return documents.get_all_text_chunks(
            target_size=500,
            include_metadata=True
        )
```

## Getting Help

If you need assistance with migration:

- 📖 [Full Documentation](https://docs.cerevox.ai)
- 💬 [Discord Community](https://discord.gg/cerevox)
- 📧 [Email Support](mailto:support@cerevox.ai)
- 🐛 [GitHub Issues](https://github.com/CerevoxAI/cerevox-python/issues) 