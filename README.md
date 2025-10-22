<p align="center">
  <a href="https://cerevox.ai">
    <img height="120" src="https://raw.githubusercontent.com/CerevoxAI/assets/refs/heads/main/cerevox-python.png" alt="Cerevox Logo">
  </a>
</p>

<h1 align="center">Cerevox - The Data Layer for AI Agents 🧠 ⚡</h1>

<p align="center">
  <strong>Flagship Results @ Mini Cost</strong><br>
  <i>Data Parsing (Lexa) • Data Search (Hippo) • Enterprise-grade • Built for AI</i>
</p>

<p align="center">
  <strong>🎯 80% cost reduction • 99.5% accuracy match • 10x more requests</strong><br>
  <i>Precision retrieval delivers 70% smaller context — only relevant chunks, zero noise</i>
</p>

<p align="center">
  <a href="https://github.com/cerevoxAI/cerevox-python/actions"><img src="https://img.shields.io/github/actions/workflow/status/CerevoxAI/cerevox-python/ci.yml" alt="CI Status"></a>
  <a href="https://codecov.io/gh/CerevoxAI/cerevox-python"><img src="https://codecov.io/gh/CerevoxAI/cerevox-python/branch/main/graph/badge.svg" alt="Code Coverage"></a>
  <a href="https://github.com/cerevoxAI/cerevox-python"><img src="https://qlty.sh/badges/8be43bff-101e-4701-a522-84b27c9e0f9b/maintainability.svg" alt="Maintainability"></a>
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

**Official Python SDK for [Cerevox](https://cerevox.ai) - The Data Layer for AI Agents**

> 🎯 **Three powerful APIs in one SDK:**
> - **Lexa** - Data parsing: Extract structured data from documents with SOTA accuracy
> - **Hippo** - Data search: Semantic search & Q&A over document collections
> - **Account** - Enterprise user management and authentication

## 📦 Installation

```bash
pip install cerevox
```

## 📋 Requirements

- Python 3.9+
- API key from [Cerevox](https://cerevox.ai)

## 🚀 Quick Start

### 📄 Data Parsing with Lexa

Parse documents into structured data for your AI agents:

```python
from cerevox import Lexa

# Parse documents
client = Lexa(api_key="your-api-key")
documents = client.parse(["document.pdf", "report.docx"])

print(f"Extracted {len(documents[0].content)} characters")
print(f"Found {len(documents[0].tables)} tables")

# Get chunks optimized for vector databases
chunks = documents.get_all_text_chunks(target_size=500)
print(f"Ready for embedding: {len(chunks)} chunks")
```

### 🦛 Data Search with Hippo

Enable AI agents to search and query your document collections:

```python
from cerevox import Hippo

# Initialize RAG client
hippo = Hippo(api_key="your-api-key")

# Create a folder and upload documents
hippo.create_folder("docs", "My Documents")
hippo.upload_file("docs", "document.pdf")

# Create a chat and ask questions
chat = hippo.create_chat("docs")
response = hippo.submit_ask(
    chat["chat_id"],
    "What are the key findings in this document?"
)

print(response["response"])
# Includes source citations and confidence scores!
```

### ⚡ Async Processing (Recommended)

Both Lexa and Hippo support async/await for high-performance AI agent workflows:

```python
import asyncio
from cerevox import AsyncLexa, AsyncHippo

async def main():
    # Document parsing
    async with AsyncLexa(api_key="your-api-key") as lexa:
        documents = await lexa.parse(["doc1.pdf", "doc2.pdf"])
        print(f"Parsed {len(documents)} documents")

    # RAG operations
    async with AsyncHippo(api_key="your-api-key") as hippo:
        await hippo.create_folder("docs", "Documents")
        result = await hippo.upload_file("docs", "document.pdf")

        chat = await hippo.create_chat("docs")
        answer = await hippo.submit_ask(
            chat["chat_id"],
            "Summarize this document"
        )
        print(answer["response"])

asyncio.run(main())
```

## ✨ Features

### 📄 **Lexa - Data Parsing**
- **SOTA Accuracy** with cutting-edge ML models for document parsing
- **12+ File Formats** - PDF, DOCX, PPTX, HTML, images, and more
- **Advanced Table Extraction** preserving structure and formatting
- **Vector DB Optimized** chunks for AI agent knowledge bases
- **7+ Cloud Storage** integrations (S3, SharePoint, Google Drive, etc.)
- **Rich Metadata** extraction including images, formatting, and structure

### 🦛 **Hippo - Data Search**
- **Precision Retrieval** - 70% smaller context with only relevant chunks, zero noise
- **Semantic Search** over document collections for AI agents
- **AI-Powered Q&A** with source citations and confidence scores
- **Folder Organization** for structured document management
- **Chat Sessions** for conversational AI agent interactions
- **Multi-Format Upload** from files, URLs, or bytes
- **Real-time Processing** with progress tracking
- **Source Attribution** for reliable AI agent responses

### 🚀 **Enterprise Ready**
- **Flagship Results @ Mini Cost** - 80% cost reduction with 99.5% accuracy match
- **10x More Requests** with efficient precision retrieval
- **Native Async Support** with concurrent processing
- **Automatic Retries** and error recovery
- **Framework Agnostic** - works with Django, Flask, FastAPI
- **Full Type Safety** with Pydantic v2 models
- **90% Test Coverage** with comprehensive test suites

## 📋 Examples

Explore comprehensive examples in the `examples/` directory:

| Example | Description |
|---------|-------------|
| **[`account_hippo_usage.py`](examples/account_hippo_usage.py)** | Complete workflow: authentication, RAG operations, Q&A |
| **[`unified_client_example.py`](examples/unified_client_example.py)** | Combined usage of Lexa, Hippo, and Account APIs |
| **[`lexa_examples.py`](examples/lexa_examples.py)** | Document parsing functionality demonstration |
| **[`vector_db_preparation.py`](examples/vector_db_preparation.py)** | Vector database chunking and integration patterns |
| **[`async_examples.py`](examples/async_examples.py)** | Advanced async processing techniques |
| **[`document_examples.py`](examples/document_examples.py)** | Document analysis and manipulation features |
| **[`cloud_integrations.py`](examples/cloud_integrations.py)** | Cloud storage service integrations |

### 🚀 Run Examples

```bash
# Clone and explore
git clone https://github.com/CerevoxAI/cerevox-python.git
cd cerevox-python

export CEREVOX_API_KEY="your-api-key"

# Run demos
python examples/account_hippo_usage.py    # RAG + Account workflow
python examples/unified_client_example.py # All three APIs
python examples/lexa_examples.py          # Document parsing
python examples/vector_db_preparation.py  # Vector DB integration
python examples/async_examples.py         # Async features
```

## 🎯 Use Cases

**Data Parsing (Lexa)**
- Extract structured data from contracts, invoices, reports for AI agent processing
- Prepare documents for AI agent knowledge bases and vector databases
- Analyze document structure, tables, and metadata
- Integrate with cloud storage for automated AI agent data pipelines

**Data Search (Hippo)**
- Enable AI agents to search and retrieve from internal documentation with precision retrieval
- Power AI agent knowledge retrieval with 70% smaller, more relevant context
- Build AI agents with intelligent document-backed responses at 80% lower cost
- Extract insights from large document collections for AI analysis

## 📚 Documentation

### 📖 **Guides & Tutorials**
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[Vector Database Integration](docs/vector-database-integration.md)** - RAG and vector DB setup
- **[Advanced Examples](docs/advanced-examples.md)** - Real-world usage patterns
- **[Migration Guide](docs/migration-guide.md)** - Migrate from other tools

### 🔗 **External Resources**
- **[Full Documentation](https://docs.cerevox.ai)** - Comprehensive guides
- **[Interactive API Docs](https://data.cerevox.ai/docs)** - Try the API
- **[Discord Community](https://discord.gg/cerevox)** - Get help and discuss

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
- [API Reference](docs/api-reference.md)
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

---

<strong>⭐ Star us on GitHub if Cerevox helped your project!</strong><br>
Made with ❤️ by the Cerevox team<br>
Happy Building! 🔍 🦛 ✨
