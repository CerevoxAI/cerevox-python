# Changelog

All notable changes to the Cerevox Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial open-source release preparation
- Professional packaging structure with pyproject.toml
- Comprehensive documentation and examples

## [0.1.0] - 2025-06-06

### Added
- Initial release of Cerevox Python SDK
- Synchronous client (`Lexa`) for document processing
- Asynchronous client (`AsyncLexa`) for high-performance processing
- Document batch processing with progress tracking
- Automatic job polling and completion handling
- Structured document loading with `Document` and `DocumentBatch` classes
- Intelligent document chunking for vector database preparation
- Support for multiple file formats (PDF, DOCX, XLSX, etc.)
- Cloud storage integrations (Google Drive, S3, Box, Dropbox, etc.)
- Comprehensive error handling and retry logic
- Rich progress bars and terminal output
- Full type hints and Pydantic model validation
- Async/await support throughout the library
- Advanced search capabilities across documents
- Multiple export formats (JSON, Markdown, combined text)
- Professional documentation and examples

### Features
- **Document Processing**: Upload and process documents with automatic completion
- **Batch Operations**: Process multiple files with progress tracking
- **Vector DB Preparation**: Intelligent chunking optimized for embeddings
- **Cloud Integration**: Built-in support for 7+ cloud storage services
- **Async Support**: Full async/await support for high-performance applications
- **Type Safety**: Complete type hints and runtime validation
- **Error Handling**: Comprehensive error handling with detailed messages
- **Progress Tracking**: Real-time progress updates for batch operations
- **Document Search**: Advanced search functionality across processed documents
- **Export Options**: Multiple formats for different use cases

### Dependencies
- Python >= 3.9
- requests >= 2.28.0
- aiohttp >= 3.8.0
- aiofiles >= 23.0.0
- pandas >= 1.5.0
- pydantic >= 2.0.0
- beautifulsoup4 >= 4.11.0

[Unreleased]: https://github.com/CerevoxAI/cerevox-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/CerevoxAI/cerevox-python/releases/tag/v0.1.0 