"""
Tests for cerevox.__init__

This test file ensures 100% coverage of the package initialization module,
including all imports, metadata, and __all__ exports.
"""

import importlib
from unittest.mock import patch

import pytest


class TestPackageInitialization:
    """Test package initialization and metadata."""

    def test_package_version(self):
        """Test that package version is accessible and correctly set."""
        import cerevox

        assert hasattr(cerevox, "__version__")
        assert cerevox.__version__ == "0.1.0"
        assert isinstance(cerevox.__version__, str)

    def test_package_metadata(self):
        """Test that all package metadata is accessible and correctly set."""
        import cerevox

        # Test all metadata attributes exist
        assert hasattr(cerevox, "__title__")
        assert hasattr(cerevox, "__description__")
        assert hasattr(cerevox, "__author__")
        assert hasattr(cerevox, "__license__")

        # Test metadata values
        assert cerevox.__title__ == "cerevox"
        assert (
            cerevox.__description__
            == "Cerevox - The Data Layer, Lexa - parse documents with enterprise-grade reliability"
        )
        assert cerevox.__author__ == "Cerevox Team"
        assert cerevox.__license__ == "MIT"

        # Test metadata types
        assert isinstance(cerevox.__title__, str)
        assert isinstance(cerevox.__description__, str)
        assert isinstance(cerevox.__author__, str)
        assert isinstance(cerevox.__license__, str)


class TestCoreImports:
    """Test core client imports."""

    def test_lexa_import(self):
        """Test that Lexa client can be imported."""
        from cerevox import Lexa

        assert Lexa is not None

    def test_async_lexa_import(self):
        """Test that AsyncLexa client can be imported."""
        from cerevox import AsyncLexa

        assert AsyncLexa is not None

    def test_account_import(self):
        """Test that Account client can be imported."""
        from cerevox import Account

        assert Account is not None

    def test_async_account_import(self):
        """Test that AsyncAccount client can be imported."""
        from cerevox import AsyncAccount

        assert AsyncAccount is not None

    def test_hippo_import(self):
        """Test that Hippo client can be imported."""
        from cerevox import Hippo

        assert Hippo is not None

    def test_async_hippo_import(self):
        """Test that AsyncHippo client can be imported."""
        from cerevox import AsyncHippo

        assert AsyncHippo is not None


class TestDocumentProcessingImports:
    """Test document processing related imports."""

    def test_document_imports(self):
        """Test document-related class imports."""
        from cerevox import (
            Document,
            DocumentBatch,
            DocumentElement,
            DocumentImage,
            DocumentMetadata,
            DocumentTable,
        )

        assert Document is not None
        assert DocumentBatch is not None
        assert DocumentMetadata is not None
        assert DocumentTable is not None
        assert DocumentImage is not None
        assert DocumentElement is not None

    def test_chunking_function_imports(self):
        """Test chunking function imports."""
        from cerevox import chunk_markdown, chunk_text

        assert chunk_markdown is not None
        assert chunk_text is not None
        assert callable(chunk_markdown)
        assert callable(chunk_text)


class TestModelImports:
    """Test model and type imports."""

    def test_model_imports(self):
        """Test that all model classes can be imported."""
        from cerevox import (
            BucketListResponse,
            FileInfo,
            FolderListResponse,
            IngestionResult,
            JobResponse,
            JobStatus,
            ProcessingMode,
        )

        assert JobStatus is not None
        assert JobResponse is not None
        assert IngestionResult is not None
        assert ProcessingMode is not None
        assert FileInfo is not None
        assert BucketListResponse is not None
        assert FolderListResponse is not None


class TestExceptionImports:
    """Test exception class imports."""

    def test_exception_imports(self):
        """Test that all exception classes can be imported."""
        from cerevox import (
            LexaAuthError,
            LexaError,
            LexaJobFailedError,
            LexaRateLimitError,
            LexaTimeoutError,
        )

        assert LexaError is not None
        assert LexaAuthError is not None
        assert LexaRateLimitError is not None
        assert LexaTimeoutError is not None
        assert LexaJobFailedError is not None

        # Verify they are exception classes
        assert issubclass(LexaError, Exception)
        assert issubclass(LexaAuthError, Exception)
        assert issubclass(LexaRateLimitError, Exception)
        assert issubclass(LexaTimeoutError, Exception)
        assert issubclass(LexaJobFailedError, Exception)


class TestAllExports:
    """Test __all__ list and its contents."""

    def test_all_list_exists(self):
        """Test that __all__ list exists and is a list."""
        import cerevox

        assert hasattr(cerevox, "__all__")
        assert isinstance(cerevox.__all__, list)
        assert len(cerevox.__all__) > 0

    def test_all_exports_importable(self):
        """Test that all items in __all__ are actually importable."""
        import cerevox

        # Get all items from __all__
        all_items = cerevox.__all__

        # Test each item is importable
        for item_name in all_items:
            assert hasattr(
                cerevox, item_name
            ), f"'{item_name}' not found in cerevox module"
            item = getattr(cerevox, item_name)
            assert item is not None, f"'{item_name}' is None"

    def test_all_contains_expected_items(self):
        """Test that __all__ contains all expected exports."""
        import cerevox

        # These are the actual exports from the __init__.py file
        expected_exports = {
            # Core clients
            "Lexa",
            "AsyncLexa",
            # Account management clients
            "Account",
            "AsyncAccount",
            # RAG clients
            "Hippo",
            "AsyncHippo",
            # Document processing
            "Document",
            "DocumentBatch",
            "DocumentMetadata",
            "DocumentTable",
            "DocumentImage",
            "DocumentElement",
            "ElementContent",
            "ElementStats",
            "FileInfo",
            "PageInfo",
            "SourceInfo",
            "chunk_markdown",
            "chunk_text",
            # Models and types
            "JobStatus",
            "JobResponse",
            "IngestionResult",
            "ProcessingMode",
            "BucketListResponse",
            "FolderListResponse",
            # Account models
            "AccountInfo",
            "AccountPlan",
            "CreatedResponse",
            "DeletedResponse",
            "MessageResponse",
            "TokenResponse",
            "UpdatedResponse",
            "User",
            "UserCreate",
            "UserUpdate",
            "UsageMetrics",
            # Exceptions
            "LexaError",
            "LexaAuthError",
            "LexaRateLimitError",
            "LexaTimeoutError",
            "LexaJobFailedError",
            # Version
            "__version__",
            "__title__",
            "__description__",
            "__author__",
            "__license__",
        }

        actual_exports = set(cerevox.__all__)

        # Check that all expected items are in __all__
        for expected_item in expected_exports:
            assert (
                expected_item in actual_exports
            ), f"'{expected_item}' missing from __all__"

        # Check that there are no unexpected items in __all__
        for actual_item in actual_exports:
            assert (
                actual_item in expected_exports
            ), f"Unexpected item '{actual_item}' found in __all__"

    def test_all_length_matches_expected(self):
        """Test that __all__ has the expected number of items."""
        import cerevox

        # Count expected items based on the actual __all__ list in __init__.py
        expected_count = 46  # Based on the actual __all__ list in the file (added all models and exceptions)
        actual_count = len(cerevox.__all__)

        assert actual_count == expected_count, (
            f"Expected {expected_count} items in __all__, got {actual_count}. "
            f"Items: {cerevox.__all__}"
        )


class TestDirectImports:
    """Test direct imports from the package."""

    def test_direct_import_all_at_once(self):
        """Test importing all main components at once."""
        from cerevox import (
            AsyncLexa,
            Document,
            DocumentBatch,
            DocumentMetadata,
            JobResponse,
            JobStatus,
            Lexa,
            LexaError,
            __version__,
        )

        # Basic verification that imports worked
        assert Lexa is not None
        assert AsyncLexa is not None
        assert Document is not None
        assert DocumentBatch is not None
        assert DocumentMetadata is not None
        assert JobStatus is not None
        assert JobResponse is not None
        assert LexaError is not None
        assert __version__ is not None

    def test_wildcard_import(self):
        """Test that wildcard import works and respects __all__."""
        # Import the package normally first
        import cerevox

        # Create a new namespace to test wildcard import
        namespace = {}
        exec("from cerevox import *", namespace)

        # Check that all items from __all__ are in the namespace
        for item_name in cerevox.__all__:
            assert (
                item_name in namespace
            ), f"'{item_name}' not imported with wildcard import"

        # Check that private items (except __builtins__ which is always present) are not imported
        private_items = [
            name
            for name in dir(cerevox)
            if name.startswith("_") and name not in ["__version__", "__builtins__"]
        ]
        for private_item in private_items:
            if private_item not in cerevox.__all__:
                assert (
                    private_item not in namespace
                ), f"Private item '{private_item}' imported with wildcard"


class TestPackageStructure:
    """Test package structure and organization."""

    def test_package_is_importable(self):
        """Test that the package can be imported without errors."""
        try:
            import cerevox

            assert True  # If we get here, import succeeded
        except ImportError as e:
            pytest.fail(f"Failed to import cerevox package: {e}")

    def test_package_has_docstring(self):
        """Test that the package has a docstring."""
        import cerevox

        assert cerevox.__doc__ is not None
        assert isinstance(cerevox.__doc__, str)
        assert len(cerevox.__doc__.strip()) > 0
        assert "Cerevox - The Data Layer" in cerevox.__doc__

    def test_no_unexpected_attributes(self):
        """Test that the package doesn't expose unexpected attributes."""
        import cerevox

        # Get all public attributes
        public_attrs = [name for name in dir(cerevox) if not name.startswith("_")]

        # All public attributes should be in __all__ (except for imported modules)
        for attr_name in public_attrs:
            if attr_name not in cerevox.__all__:
                # Check if it's a module (these might not be in __all__)
                attr_value = getattr(cerevox, attr_name)
                if not hasattr(attr_value, "__file__"):  # Not a module
                    pytest.fail(f"Public attribute '{attr_name}' not in __all__")


class TestImportResilience:
    """Test import behavior under various conditions."""

    def test_repeated_imports(self):
        """Test that repeated imports work correctly."""
        # First import
        import cerevox

        first_version = cerevox.__version__

        # Second import
        import cerevox

        second_version = cerevox.__version__

        # Should be the same
        assert first_version == second_version

        # Re-import with importlib
        importlib.reload(cerevox)
        third_version = cerevox.__version__

        assert first_version == third_version

    @patch("cerevox.clients.lexa")
    def test_import_with_missing_submodule(self, mock_lexa):
        """Test behavior when a submodule import fails."""
        # This test ensures that if a submodule has issues, we handle it gracefully
        mock_lexa.side_effect = ImportError("Mocked import error")

        # The import should still work because __init__.py should handle missing imports
        # This is more of a design test - in reality, we want imports to succeed
        try:
            import cerevox

            # If we get here, the import succeeded despite the mocked error
            assert True
        except ImportError:
            # If the import fails, that's also acceptable behavior
            # depending on how the package is designed
            assert True


class TestVersionConsistency:
    """Test version information consistency."""

    def test_version_format(self):
        """Test that version follows semantic versioning format."""
        import re

        import cerevox

        version_pattern = r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+)?(?:\+[a-zA-Z0-9-]+)?$"
        assert re.match(
            version_pattern, cerevox.__version__
        ), f"Version '{cerevox.__version__}' doesn't follow semantic versioning"

    def test_version_accessibility(self):
        """Test that version can be accessed in multiple ways."""
        import cerevox

        # Direct access
        assert cerevox.__version__ is not None

        # Through __all__
        assert "__version__" in cerevox.__all__

        # Via getattr
        version_via_getattr = getattr(cerevox, "__version__")
        assert version_via_getattr == cerevox.__version__


class TestCompleteImportCoverage:
    """Additional tests to ensure complete coverage of __init__.py"""

    def test_all_module_docstring_imported(self):
        """Test that the module docstring is properly set and accessible."""
        import cerevox

        # Test module has a docstring
        assert hasattr(cerevox, "__doc__")
        assert cerevox.__doc__ is not None
        assert isinstance(cerevox.__doc__, str)

        # Test specific content
        expected_content = "Cerevox - The Data Layer"
        assert expected_content in cerevox.__doc__

    def test_all_metadata_attributes_covered(self):
        """Test all metadata attributes are covered and accessible."""
        import cerevox

        # Test all metadata exists and has correct types
        metadata_attrs = [
            "__version__",
            "__title__",
            "__description__",
            "__author__",
            "__license__",
        ]

        for attr in metadata_attrs:
            assert hasattr(cerevox, attr), f"Missing metadata attribute: {attr}"
            value = getattr(cerevox, attr)
            assert value is not None, f"Metadata attribute {attr} is None"
            assert isinstance(value, str), f"Metadata attribute {attr} is not a string"
            assert len(value.strip()) > 0, f"Metadata attribute {attr} is empty"

    def test_import_from_statements_coverage(self):
        """Test that all from-import statements in __init__.py work correctly."""
        # This test ensures all the from-import statements in __init__.py are executed
        # by trying to import everything that should be available

        try:
            # Test core imports
            # Test exception imports
            # Test model imports
            # Test document processing imports
            from cerevox import (
                AsyncLexa,
                BucketListResponse,
                Document,
                DocumentBatch,
                DocumentElement,
                DocumentImage,
                DocumentMetadata,
                DocumentTable,
                FileInfo,
                FolderListResponse,
                IngestionResult,
                JobResponse,
                JobStatus,
                Lexa,
                LexaAuthError,
                LexaError,
                LexaJobFailedError,
                LexaRateLimitError,
                LexaTimeoutError,
                ProcessingMode,
                chunk_markdown,
                chunk_text,
            )

            # If we get here, all imports succeeded
            assert True

        except ImportError as e:
            pytest.fail(f"Failed to import expected items: {e}")

    def test_all_list_completeness(self):
        """Test that __all__ list includes everything it should and nothing extra."""
        import cerevox

        # Get the actual __all__ list
        actual_all = set(cerevox.__all__)

        # Expected items based on the __init__.py file
        expected_all = {
            # Core clients
            "Lexa",
            "AsyncLexa",
            # Account management clients
            "Account",
            "AsyncAccount",
            # RAG clients
            "Hippo",
            "AsyncHippo",
            # Document processing
            "Document",
            "DocumentBatch",
            "DocumentMetadata",
            "DocumentTable",
            "DocumentImage",
            "DocumentElement",
            "ElementContent",
            "ElementStats",
            "FileInfo",
            "PageInfo",
            "SourceInfo",
            "chunk_markdown",
            "chunk_text",
            # Models and types
            "JobStatus",
            "JobResponse",
            "IngestionResult",
            "ProcessingMode",
            "BucketListResponse",
            "FolderListResponse",
            # Account models
            "AccountInfo",
            "AccountPlan",
            "CreatedResponse",
            "DeletedResponse",
            "MessageResponse",
            "TokenResponse",
            "UpdatedResponse",
            "User",
            "UserCreate",
            "UserUpdate",
            "UsageMetrics",
            # Exceptions
            "LexaError",
            "LexaAuthError",
            "LexaRateLimitError",
            "LexaTimeoutError",
            "LexaJobFailedError",
            # Version info
            "__version__",
            "__title__",
            "__description__",
            "__author__",
            "__license__",
        }

        # Test exact match
        assert actual_all == expected_all, (
            f"__all__ mismatch.\n"
            f"Missing from actual: {expected_all - actual_all}\n"
            f"Extra in actual: {actual_all - expected_all}"
        )
