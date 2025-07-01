# Changelog

All notable changes to the Cerevox Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.6] - 2025-07-01

### Enhanced
- **Complete ContentElement Support**: Enhanced `_from_elements_list` method to fully handle both Pydantic ContentElement objects and dictionary formats in all processing paths
- **Metadata Extraction**: Added dual-format support for metadata extraction from first element, handling both ContentElement object properties and dictionary key access
- **Type Safety**: Updated type annotations from `List[Dict[str, Any]]` to `List[Any]` to accurately reflect support for mixed input types
- **Mixed Format Processing**: Added capability to process lists containing both ContentElement objects and dictionary elements simultaneously

### Fixed
- Resolved "ContentElement object has no attribute 'get'" error in metadata extraction phase (line 791)
- Fixed type annotation mismatch in `_from_elements_list` method parameter
- Improved error handling to gracefully handle both object attribute access and dictionary key access patterns
- Enhanced robustness when processing mixed content types in the same elements list

### Improved
- **Backward Compatibility**: Maintained full backward compatibility with existing dictionary-based API responses
- **Error Resilience**: Enhanced exception handling to cover both AttributeError (for objects) and KeyError (for dictionaries)
- **Code Documentation**: Added comprehensive inline comments explaining dual-format handling approach
- **Production Readiness**: Ensured all calling functions (`from_api_response`, `from_completed_file_data`, `DocumentBatch.from_api_response`) work seamlessly with ContentElement objects

## [0.1.5] - 2025-07-01

### Fixed
- Fixed critical bug in document parsing where ContentElement objects (Pydantic models) were incorrectly handled as dictionaries
- Resolved "ContentElement object has no attribute 'get'" warnings during benchmark execution
- Improved type detection in `_from_elements_list` method to properly distinguish between Pydantic models and dictionary formats
- Enhanced error handling for malformed elements during document processing

### Added
- Comprehensive test coverage for ContentElement object handling in document parsing
- Enhanced test `test_from_elements_list_content_element` covering both Pydantic ContentElement objects and dictionary formats
- Test coverage for mixed element processing scenarios (ContentElement + dictionary format)
- Robust type checking for dual-format element processing

### Testing
- Improved test coverage for `_from_elements_list` method in document_loader.py (lines 803-831)
- Added validation tests for ContentElement source data extraction including file info, page info, and element statistics
- Enhanced coverage of dual-format element processing (Pydantic models vs dictionary format)

## [0.1.4] - 2025-07-01

### Fixed
- Fixed Pydantic validation error in `ContentInfo` model when API responses contain content without HTML field
- Made `html` field optional in `ContentInfo` to handle variable API response formats
- Improved robustness of document parsing when HTML content is not available

## [0.1.3] - 2025-07-01

### Added
- New `BasicFileInfo` model for handling simplified file information during early processing stages

### Fixed
- Pydantic validation error in `JobResponse` model when files are in early processing stages
- Updated `JobResponse.files` field to support `BasicFileInfo`, `FileProcessingInfo`, and `CompletedFileData` types

## [0.1.2] - 2025-06-16

### Added
- Comprehensive test suites for all core modules (document_loader, async_lexa, lexa.py)
- Missing Lexa class with complete documentation and array format coverage
- Enhanced DocumentBatch documentation with missing properties and usage examples
- Comprehensive Table of Contents across all documentation files
- Improved Python 3.9 and 3.10 compatibility

### Fixed
- Processing mode documentation and example formatting issues
- Shebang line in examples/document_examples.py for consistency
- README.md requirements section formatting issues
- Testing issues for Python 3.9 and 3.10 compatibility

### Changed
- Restructured API reference documentation with improved organization
- Repositioned performance comparison to top of migration guide for better UX
- Enhanced standalone functions section with API key notes and clean signatures

### Testing
- Achieved 100% test coverage across core modules
- Implemented comprehensive test suites for document_loader, async_lexa, and lexa.py

## [0.1.1] - 2025-06-06

### Added
- Tagged release with initial version bump

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

[Unreleased]: https://github.com/CerevoxAI/cerevox-python/compare/v0.1.6...HEAD
[0.1.6]: https://github.com/CerevoxAI/cerevox-python/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/CerevoxAI/cerevox-python/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/CerevoxAI/cerevox-python/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/CerevoxAI/cerevox-python/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/CerevoxAI/cerevox-python/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/CerevoxAI/cerevox-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/CerevoxAI/cerevox-python/releases/tag/v0.1.0 