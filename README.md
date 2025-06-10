<p align="center">
  <a href="https://cerevox.ai/lexa">
    <img height="120" src="https://raw.githubusercontent.com/CerevoxAI/assets/refs/heads/main/cerevox-python.png" alt="Cerevox Logo">
  </a>
</p>

<h1 align="center">Cerevox - The Data Layer 🧠 ⚡</h1>

<p align="center">
  <strong>Parse documents with enterprise-grade reliability</strong><br>
  <i>AI-powered • Highest Accuracy • Vector DB ready</i>
</p>

<p align="center">
  <a href="https://github.com/cerevoxAI/cerevox-python/actions"><img src="https://img.shields.io/github/actions/workflow/status/CerevoxAI/cerevox-python/ci.yml" alt="CI Status"></a>
  <a href="https://codecov.io/gh/CerevoxAI/cerevox-python"><img src="https://codecov.io/gh/CerevoxAI/cerevox-python/branch/main/graph/badge.svg" alt="Code Coverage"></a>
  <a href="https://pypi.org/project/cerevox/"><img src="https://img.shields.io/pypi/v/cerevox?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/cerevox/"><img src="https://img.shields.io/pypi/pyversions/cerevox" alt="Python versions"></a>
  <a href="https://github.com/cerevoxAI/cerevox-python/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  
</p>

- <a href="#-installation">Installation</a>
- <a href="#-quick-start">Quick Start</a>  
- <a href="#-features">Features</a> 
- <a href="#-examples">Examples</a>
- <a href="#-documentation">Documentation</a>
- <a href="#-support--community">Support</a>
---

**Official Python SDK for [Lexa](https://cerevox.ai/lexa) - Parse documents into structured data**

> 🎯 **Perfect for**: RAG applications, document analysis, data extraction, and vector database preparation

## 📦 Installation
```bash
pip install cerevox
```
**System Requirements:**
- Python 3.9+
- API key from [Cerevox](https://cerevox.ai/lexa)
## 🚀 Quick Start

### Get started in 30 seconds:

```python
from cerevox import Lexa

# Parse a document
client = Lexa(api_key="your-api-key")
documents = client.parse(["document.pdf"])

print(f"Extracted {len(documents[0].content)} characters")
print(f"Found {len(documents[0].tables)} tables")
```

### Async Processing (Recommended):

```python
import asyncio
from cerevox import AsyncLexa

async def main():
    async with AsyncLexa(api_key="your-api-key") as client:
        documents = await client.parse(["document.pdf", "report.docx"])
        
        # Get chunks optimized for vector databases
        chunks = documents.get_all_text_chunks(target_size=500)
        print(f"Ready for embedding: {len(chunks)} chunks")

asyncio.run(main())
```

<details>
<summary><strong>🎥 See It In Action</strong></summary>

### Document Processing Pipeline
```
📄 Input Document → 🧠 AI Processing → 📊 Structured Output → 🔍 Vector Ready
```

### Sample Output Structure
```json
{
  "filename": "financial_report.pdf",
  "content": "Q4 financial results show...",
  "tables": [
    {
      "headers": ["Quarter", "Revenue", "Growth"],
      "rows": [["Q4", "$2.3M", "15%"]]
    }
  ],
  "metadata": {
    "pages": 12,
    "confidence": 0.998,
    "processing_time": 2.3
  },
  "chunks": [
    {
      "content": "Executive Summary: Q4 results...",
      "metadata": {"page": 1, "section": "summary"}
    }
  ]
}
```

</details>

## ✨ Features

### 🚀 **Performance & Scale**
- **10x Faster** than traditional solutions
- **Native Async Support** with concurrent processing
- **Enterprise-grade** reliability with automatic retries

### 🧠 **AI-Powered Extraction**
- **SOTA Accuracy** with cutting-edge ML models
- **Advanced Table Extraction** preserving structure and formatting
- **12+ File Formats** including PDF, DOCX, PPTX, HTML, and more

### 🔗 **Integration Ready**
- **Vector Database Optimized** chunks for RAG applications
- **7+ Cloud Storage** integrations (S3, SharePoint, Google Drive, etc.)
- **Framework Agnostic** works with Django, Flask, FastAPI

### 👨‍💻 **Developer Experience**
- **Intuitive API** with full type hints and comprehensive examples
- **Rich Metadata** extraction including images, formatting, and structure
- **Smart Search** across documents and batches

<details>
<summary><strong>🧩 Intelligent Vector Database Preparation</strong></summary>

Engineered specifically for vector databases and RAG applications

### 🎯 **Smart Chunking Features**
-  **Structure-Aware**: Preserves headers, paragraphs, code blocks, and logical document boundaries
-  **Precise Control**: Configurable target sizes with tolerance for optimal embedding performance
-  **Format-Aware**: Maintains markdown formatting, code syntax, and table structures
-  **Performance-First**: Built-in async processing with no manual post-processing required
-  **Rich Context**: Full document metadata for enhanced retrieval and search relevance

### 🚀 **Quick Start Examples**
```python
from cerevox import AsyncLexa, chunk_markdown, chunk_text

# 🎯 Method 1: Direct Vector DB Preparation (Recommended)
async  with  AsyncLexa()  as client:
	documents =  await client.parse(["document.pdf",  "report.docx"])
	
	# Get optimized chunks for vector databases
	text_chunks = documents.get_all_text_chunks(
		target_size=500,  # Performant for most embedding models
		include_metadata=True # Rich context for retrieval
	)
	markdown_chunks = documents.get_all_markdown_chunks(
		target_size=800,  # Larger chunks for formatted content
		tolerance=0.1  # ±10% size flexibility
	)

	# 🔧 Method 2: Standalone Chunking Functions
	chunks =  chunk_markdown(markdown_content,  target_size=500)
	chunks =  chunk_text(plain_text,  target_size=300)
```
### 🗄️ **Vector Database Integration**
```python
async  with  AsyncLexa()  as client:
	documents =  await client.parse(["doc.pdf"])
	chunks = documents.get_all_text_chunks(target_size=512)

	for chunk in chunks:
		# Pinecone Integration
		embedding =  generate_embedding(chunk['content'])
		index.upsert([{
			'id': f"{chunk['document_filename']}_{chunk['chunk_index']}",
			'values': embedding,
			'metadata': chunk # Includes filename, page, element_type, etc.
		}])

		# ChromaDB Integration
		collection.add(
			documents=[chunk['content']  for chunk in chunks],
			metadatas=[chunk for chunk in chunks],
			ids=[f"doc_{i}"  for i in  range(len(chunks))]
		)

```
</details>

<details>
<summary><strong>☁️ Cloud Storage Integrations - Coming Soon!</strong></summary>

**Coming Soon!**
Connect and parse documents from **7+ cloud storage services** just setup authentication on [Cerevox](https://www.cerevox.ai/lexa):
```python
async  with  AsyncLexa()  as client:
	# Amazon S3
	s3_docs =  await client.parse_s3_folder(
		bucket_name="my-bucket",
		folder_path="documents/"
	)

	# Microsoft SharePoint
	sharepoint_docs =  await client.parse_sharepoint_folder(
		drive_id="drive-id",
		folder_id="folder-id"
	)

	# Also supports: Box, Dropbox, Google Drive, Salesforce, Sendme

```

**Supported Services:** Coming Soon!

- 🗄️ **Amazon S3** - Bucket and folder parsing
- 📦 **Box** - Enterprise file management
- 💾 **Dropbox** - Personal and business accounts
- 📁 **Google Drive** - File and folder processing
- 🏢 **Microsoft SharePoint** - Sites, drives, and folders
- 🤝 **Salesforce** - CRM document processing
- 📤 **Sendme** - Secure file transfer integration
</details>

## 📋 **Examples**
Explore comprehensive examples in the `examples/` directory:

| Example | Description |
|---------|-------------|
| **`lexa_examples.py`** | Complete SDK functionality demonstration |
| **`vector_db_preparation.py`** | Vector database chunking and integration patterns |
| **`async_examples.py`** | Advanced async processing and cloud integrations |
| **`document_examples.py`** | Document analysis and manipulation features |
| **`cloud_integrations.py`** | All cloud storage service integrations |

### 🚀 **Run the Complete Demo**
```bash
# Clone and explore
git clone https://github.com/CerevoxAI/cerevox-python.git

cd cerevox-python

export  CEREVOX_API_KEY="your-api-key"

# Run comprehensive demos
python  examples/async_examples.py  # Async features
python  examples/cloud_integrations.py  # Cloud Integrations
python  examples/document_examples.py  # Document analysis
python  examples/vector_db_preparation.py  # Vector DB preparation
```

<details>
<summary><strong>🧪 Advanced Examples</strong></summary>

### 🔍 **Content Analysis & Search**
```python
# Advanced document analysis
doc = documents[0]

# Extract statistics
stats = doc.get_statistics()
print(f"Characters: {stats['characters']}")
print(f"Words: {stats['words']}")
print(f"Sentences: {stats['sentences']}")

# Content search with metadata
matches = doc.search_content("revenue",  include_metadata=True)

for match in matches:
	print(f"Found on page {match['page_number']}: {match['context']}")

# Batch analysis
similarity_matrix = documents.get_content_similarity_matrix()
key_phrases = documents.extract_key_phrases(top_n=10)
```
### 🗄️ **Table Extraction & Processing**
```python
# Extract and analyze tables
all_tables = documents.get_all_tables()

print(f"Found {len(all_tables)} tables across documents")

# Convert to pandas for analysis
df_tables = documents.to_pandas_tables()

for filename, tables in df_tables.items():
	print(f"📄 {filename}: {len(tables)} tables")

	for table in tables:
		print(f" Table shape: {table.shape}")

# Export tables to CSV
documents.export_tables_to_csv("exported_tables/")
```
### ⚡ **Performance Optimization**
```python

# Configure for high-performance processing
async with AsyncLexa(
	api_key="your-api-key",
	max_concurrent=20,  # Increase parallel processing
	timeout=120.0,  # Extended timeout for large files
	max_retries=5  # Enhanced error resilience
) as client:

	# Batch processing with progress tracking
	def  progress_callback(status):
		print(f"📊 {status.status} - Processing...")

	documents = await client.parse(
		files=large_file_list,
		mode=ProcessingMode.ADVANCED,
		progress_callback=progress_callback
	)
```
</details>

## 📚 Documentation

For complete API documentation, visit:

- 📖 **[Full Documentation](https://docs.cerevox.ai)** - Comprehensive guides and tutorials
- 🔧 **[API Reference](https://data.cerevox.ai/docs)** - Interactive API documentation
- 💬 **[Discord Community](https://discord.gg/cerevox)** - Get help from the community

<details>
<summary><strong>📋 API Reference</strong></summary>

### AsyncLexa(api_key: [string], [options: [dict]])

The main async client for document processing with enterprise-grade reliability.

#### api_key

* _**Required**_
* Type: [string]
* Values: `<your cerevox api key>`

Your Cerevox API key obtained from [Cerevox](https://cerevox.ai/lexa).

#### options

##### max_concurrent

* _Optional_
* Type: [int]
* Default: `10`

Maximum number of concurrent processing jobs.

##### timeout

* _Optional_
* Type: [float]
* Default: `60.0`

Request timeout in seconds for API calls.

##### max_retries

* _Optional_
* Type: [int]
* Default: `3`

Maximum number of retry attempts for failed requests.

### AsyncLexa Methods

#### parse(files: [list], [options: [dict]])

Parse documents from local files or file paths.

##### files

* _**Required**_
* Type: [list]&lt;[string]&gt;
* Values: `["path/to/file.pdf", "document.docx"]`

List of file paths to parse.

##### options

###### progress_callback

* _Optional_
* Type: [function]
* Default: `None`

Callback function to track parsing progress. Receives status updates.

###### mode

* _Optional_
* Type: [string]
* Default: `'STANDARD'`
* Values: `'STANDARD'`, `'ADVANCED'`

Processing mode for document parsing.

#### parse_urls(urls: [list], [options: [dict]])

Parse documents from URLs.

##### urls

* _**Required**_
* Type: [list]&lt;[string]&gt;
* Values: `["https://example.com/doc.pdf"]`

List of URLs pointing to documents to parse.

##### options

Same as `parse()` method options.

### Document Object

Individual document with rich metadata and content access.

#### Properties

##### filename

* Type: [string]
* Description: Original filename of the document

##### file_type

* Type: [string]
* Description: Document type (e.g., 'pdf', 'docx', 'html')

##### page_count

* Type: [int]
* Description: Number of pages in the document

##### content

* Type: [string]
* Description: Plain text content of the document

##### elements

* Type: [list]&lt;[dict]&gt;
* Description: Structured document elements with metadata

##### tables

* Type: [list]&lt;[dict]&gt;
* Description: Extracted tables from the document

#### Methods

##### to_markdown()

* Returns: [string]
* Description: Convert document to formatted markdown

##### to_html()

* Returns: [string]
* Description: Convert document to HTML format

##### to_dict()

* Returns: [dict]
* Description: Convert document to dictionary format

##### search_content(query: [string], [options: [dict]])

Search for content within the document.

###### query

* _**Required**_
* Type: [string]

The search query string.

###### options

###### include_metadata

* _Optional_
* Type: [bool]
* Default: `False`

Include metadata in search results.

##### get_elements_by_page(page_number: [int])

* Returns: [list]&lt;[dict]&gt;
* Description: Get all elements from a specific page

###### page_number

* _**Required**_
* Type: [int]
* Values: `1, 2, 3...`

Page number to retrieve elements from.

##### get_elements_by_type(element_type: [string])

* Returns: [list]&lt;[dict]&gt;
* Description: Filter elements by type

###### element_type

* _**Required**_
* Type: [string]
* Values: `'table'`, `'paragraph'`, `'header'`, etc.

Type of elements to retrieve.

##### get_statistics()

* Returns: [dict]
* Description: Get document statistics including character count, word count, etc.

### DocumentBatch Object

Collection of documents with batch operations.

#### Properties

##### total_pages

* Type: [int]
* Description: Total pages across all documents in the batch

#### Methods

##### search_all(query: [string], [options: [dict]])

Search across all documents in the batch.

###### query

* _**Required**_
* Type: [string]

The search query string.

###### options

Same as Document `search_content()` options.

##### filter_by_type(file_type: [string])

* Returns: [list]&lt;Document&gt;
* Description: Filter documents by file type

###### file_type

* _**Required**_
* Type: [string]
* Values: `'pdf'`, `'docx'`, `'html'`, etc.

File type to filter by.

##### save_to_json(filepath: [string])

Save batch to JSON file.

###### filepath

* _**Required**_
* Type: [string]

Path where to save the JSON file.

##### to_combined_text()

* Returns: [string]
* Description: Combine all document content into single text string

##### to_combined_markdown()

* Returns: [string]
* Description: Combine all document content into single markdown string

##### to_combined_html()

* Returns: [string]
* Description: Combine all document content into single HTML string

##### get_all_text_chunks([options: [dict]])

Get optimized text chunks for vector databases.

###### options

####### target_size

* _Optional_
* Type: [int]
* Default: `500`

Target size for each chunk in characters.

####### tolerance

* _Optional_
* Type: [float]
* Default: `0.1`
* Values: `0.0 - 1.0`

Size tolerance as a percentage (e.g., 0.1 = ±10%).

####### include_metadata

* _Optional_
* Type: [bool]
* Default: `True`

Include document metadata with each chunk.

##### get_all_markdown_chunks([options: [dict]])

Get optimized markdown chunks for vector databases.

###### options

Same as `get_all_text_chunks()` plus:

####### preserve_tables

* _Optional_
* Type: [bool]
* Default: `True`

Keep table structures intact in chunks.

##### get_all_tables()

* Returns: [list]&lt;[dict]&gt;
* Description: Extract all tables from all documents

##### to_pandas_tables()

* Returns: [dict]
* Description: Convert all tables to pandas DataFrames, organized by filename

##### export_tables_to_csv(directory: [string])

Export all tables to CSV files.

###### directory

* _**Required**_
* Type: [string]

Directory path where CSV files will be saved.

### Standalone Functions

#### chunk_text(text: [string], [options: [dict]])

Chunk plain text content for vector databases.

##### text

* _**Required**_
* Type: [string]

The text content to chunk.

##### options

###### target_size

* _Optional_
* Type: [int]
* Default: `500`

Target size for each chunk in characters.

###### tolerance

* _Optional_
* Type: [float]
* Default: `0.1`

Size tolerance as a percentage.

#### chunk_markdown(markdown: [string], [options: [dict]])

Chunk markdown content while preserving structure.

##### markdown

* _**Required**_
* Type: [string]

The markdown content to chunk.

##### options

Same as `chunk_text()` plus:

###### preserve_tables

* _Optional_
* Type: [bool]
* Default: `True`

Keep table structures intact in chunks.
</details>

<details>
<summary><strong>🛡️ Error Handling & Configuration</strong></summary>

### **Robust Error Handling**
```python
from cerevox import (
	LexaAuthError,
	LexaError,
	LexaJobFailedError,
	LexaTimeoutError
)

try:
	documents =  await client.parse(files)
except LexaAuthError as e:
	print(f"❌ Authentication failed: {e.message}")

except LexaJobFailedError as e:
	print(f"❌ Job failed error: {e.message}")

except LexaTimeoutError as e:
	print(f"❌ Timeout error: {e.message} (status: {e.status_code})")

except LexaError as e:
	print(f"❌ General Lexa API error: {e.message}")

```
</details>

<details>
<summary><strong>🔄 Migration Guide</strong></summary>

### **From LlamaIndex**
```python
# Before (LlamaIndex)
documents = SimpleDirectoryReader('docs').load_data()

# After (Cerevox) - Better performance + async support
async with AsyncLexa()  as client:
	documents =  await client.parse(glob.glob('docs/*'))
	chunks = documents.get_all_text_chunks(target_size=500)
```
### **From Unstructured**
```python
# Before (Unstructured)
elements = partition_auto(filename="document.pdf")

# After (Cerevox) - More accurate tables + async support
async with AsyncLexa()  as client:
	documents =  await client.parse(["document.pdf"])
	elements = documents[0].elements # Structured with rich metadata

```
### **From Amazon Textract**
```python
# Before (Textract) - Manual polling required
response = textract.start_document_text_detection(...)

# After (Cerevox) - Automatic polling + most accurate tables
async  with  AsyncLexa()  as client:
	# Automatic polling, no manual loops needed
	documents =  await client.parse(["document.pdf"])

```
</details>

<details>
<summary><strong>🧪 Development and Testing</strong></summary>

### Setting up for Development
```bash
# Clone and install
git  clone  https://github.com/CerevoxAI/cerevox-python.git
cd  cerevox-python/python-sdk
pip  install  -e  .[dev]

# Run tests
pytest

# Run the advanced demo
export  CEREVOX_API_KEY="your-api-key"
python  examples/async_advanced.py

# Test async features
python -c "
import asyncio
from cerevox import AsyncLexa

async def test():
	async with AsyncLexa() as client:
		buckets = await client.list_s3_buckets()
		print(f'Found {len(buckets.buckets)} S3 buckets')

asyncio.run(test())
"
```
</details>

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Community

<table>
<tr>
<td>

**📖 Resources**
- [Documentation](https://docs.cerevox.ai)
- [API Reference](https://data.cerevox.ai/docs)
- [Examples](examples/)
- [Changelog](CHANGELOG.md)

</td>
<td>

**💬 Get Help**
- [Discord Community](https://discord.gg/cerevox)
- [GitHub Discussions](https://github.com/CerevoxAI/cerevox-python/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/cerevox)
- [Email Support](mailto:support@cerevox.ai)

</td>
<td>

**🐛 Issues**
- [Bug Reports](https://github.com/CerevoxAI/cerevox-python/issues/new?template=bug_report.yml)
- [Feature Requests](https://github.com/CerevoxAI/cerevox-python/issues/new?template=feature_request.yml)
- [Performance](https://github.com/CerevoxAI/cerevox-python/issues/new?template=performance.yml)
- [Security Issues](mailto:security@cerevox.ai)

</td>
</tr>
</table>

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes and migration guides.

---

<strong>⭐ Star us on GitHub if Cerevox helped your project!</strong><br>
<sub>Made with ❤️ by the Cerevox team</a></sub><br>
<sub>Happy Parsing 🔍 ✨</sub>
