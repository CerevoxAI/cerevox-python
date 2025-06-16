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

**Official Python SDK for [Lexa](https://cerevox.ai/lexa) - Parse documents into structured data**

> 🎯 **Perfect for**: RAG applications, document analysis, data extraction, and vector database preparation

## 📦 Installation

```bash
pip install cerevox
```

## 📋 Requirements

- Python 3.9+
- API key from [Cerevox](https://cerevox.ai/lexa)

## 🚀 Quick Start

### Basic Usage

```python
from cerevox import Lexa

# Parse a document
client = Lexa(api_key="your-api-key")
documents = client.parse(["document.pdf"])

print(f"Extracted {len(documents[0].content)} characters")
print(f"Found {len(documents[0].tables)} tables")
```

### Async Processing (Recommended)

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
- **Rich Metadata** extraction including images, formatting, and structure

## 📋 Examples

Explore comprehensive examples in the `examples/` directory:

| Example | Description |
|---------|-------------|
| **[`lexa_examples.py`](examples/lexa_examples.py)** | Complete SDK functionality demonstration |
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
python examples/lexa_examples.py          # Basic usage
python examples/vector_db_preparation.py  # Vector DB integration
python examples/async_examples.py         # Async features
python examples/document_examples.py      # Document analysis
python examples/cloud_integrations.py     # Cloud Integrations Coming Soon!
```



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
Happy Parsing 🔍 ✨
