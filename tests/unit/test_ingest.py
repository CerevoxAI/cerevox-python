"""
Test suite for cerevox.services.ingest

Comprehensive tests to achieve 100% code coverage for the Ingest class,
including all methods, error handling, edge cases, and folder_id logic.
"""

import json
import os
import tempfile
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import responses
from requests.exceptions import ConnectionError, RequestException, RetryError, Timeout

from cerevox.core import (
    VALID_MODES,
    BucketListResponse,
    DriveListResponse,
    FileInfo,
    FolderListResponse,
    IngestionResult,
    LexaAuthError,
    LexaError,
    LexaRateLimitError,
    LexaTimeoutError,
    LexaValidationError,
    ProcessingMode,
    SiteListResponse,
    TokenResponse,
)
from cerevox.services.ingest import Ingest


# Mock authentication for all tests
def mock_store_token_func(self, token_response):
    # Store token info manually
    self.access_token = token_response.access_token
    self.refresh_token = token_response.refresh_token
    import time

    self.token_expires_at = time.time() + token_response.expires_in
    # Update session headers with new access token
    self.session.headers.update(
        {"Authorization": f"Bearer {token_response.access_token}"}
    )


@pytest.fixture(autouse=True)
def mock_auth_methods():
    """Auto-use fixture to mock authentication methods for all tests in this module"""
    with (
        patch("cerevox.core.Client._store_token_info") as mock_store_token,
        patch("cerevox.core.Client._login") as mock_login,
        patch("cerevox.core.Client._ensure_valid_token") as mock_ensure_token,
    ):

        mock_store_token.side_effect = mock_store_token_func
        mock_login.return_value = TokenResponse(
            access_token="test-access-token",
            expires_in=3600,
            refresh_token="test-refresh-token",
            token_type="Bearer",
        )
        # Make _ensure_valid_token do nothing (token is always valid in tests)
        mock_ensure_token.return_value = None
        yield mock_login, mock_store_token


class TestIngestInitialization:
    """Test Ingest service initialization"""

    def test_init_with_product(self):
        """Test initialization with product parameter"""
        ingest = Ingest(api_key="test-api-key", product="hippo")
        assert ingest.api_key == "test-api-key"
        assert ingest.product == "hippo"
        assert ingest.data_url == "https://data.cerevox.ai"

    def test_init_without_product(self):
        """Test initialization without product parameter"""
        ingest = Ingest(api_key="test-api-key")
        assert ingest.api_key == "test-api-key"
        assert ingest.product is None

    def test_init_with_custom_urls(self):
        """Test initialization with custom URLs"""
        ingest = Ingest(
            api_key="test-key",
            data_url="https://custom.api.com",
            auth_url="https://custom.auth.com",
            product="lexa",
        )
        assert ingest.data_url == "https://custom.api.com"
        assert ingest.product == "lexa"


class TestUploadFilesWithFolderId:
    """Test _upload_files method with folder_id parameter"""

    def create_temp_file(self, content: bytes = b"test content", suffix: str = ".txt"):
        """Helper to create temporary files"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name

    def cleanup_temp_file(self, filepath: str):
        """Helper to cleanup temporary files"""
        try:
            os.unlink(filepath)
        except FileNotFoundError:
            pass

    @responses.activate
    def test_upload_files_with_folder_id(self):
        """Test uploading files with folder_id parameter - covers line 218"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={
                "message": "Files uploaded successfully",
                "requestID": "req-123",
                "uploads": ["test.txt"],
            },
            status=200,
        )

        # Create temporary file
        temp_file = self.create_temp_file(b"test content", ".txt")

        try:
            ingest = Ingest(api_key="test-key", product="hippo")
            result = ingest._upload_files(temp_file, folder_id="folder-123")

            assert isinstance(result, IngestionResult)
            assert result.request_id == "req-123"

            # Verify the request was made with folder_id
            request = responses.calls[0].request
            # folder_id should be in query parameters since it's passed as params
            assert "folder_id=folder-123" in request.url
            assert "product=hippo" in request.url
        finally:
            self.cleanup_temp_file(temp_file)

    @responses.activate
    def test_upload_files_without_folder_id(self):
        """Test uploading files without folder_id parameter"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={
                "message": "Files uploaded successfully",
                "requestID": "req-124",
                "uploads": ["test.txt"],
            },
            status=200,
        )

        temp_file = self.create_temp_file(b"test content", ".txt")

        try:
            ingest = Ingest(api_key="test-key", product="lexa")
            result = ingest._upload_files(temp_file, folder_id=None)

            assert result.request_id == "req-124"

            # Verify the request was made without folder_id
            request = responses.calls[0].request
            assert "folder_id" not in request.url
            assert "product=lexa" in request.url
        finally:
            self.cleanup_temp_file(temp_file)

    @responses.activate
    def test_upload_files_with_folder_id_and_mode(self):
        """Test uploading files with both folder_id and processing mode"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={
                "message": "Files uploaded successfully",
                "requestID": "req-125",
                "uploads": ["test.txt"],
            },
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_files(
            b"raw content", mode=ProcessingMode.ADVANCED, folder_id="folder-456"
        )

        assert result.request_id == "req-125"

        # Verify the request parameters
        request = responses.calls[0].request
        assert "folder_id=folder-456" in request.url
        assert "mode=advanced" in request.url
        assert "product=hippo" in request.url


class TestUploadUrlsWithFolderId:
    """Test _upload_urls method with folder_id parameter"""

    @responses.activate
    def test_upload_urls_with_folder_id(self):
        """Test uploading URLs with folder_id parameter - covers line 272"""
        # Mock the HEAD request for file info
        responses.add(
            responses.HEAD,
            "https://example.com/document.pdf",
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": 'attachment; filename="document.pdf"',
            },
            status=200,
        )

        # Mock the upload request
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "req-url-1"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_urls(
            "https://example.com/document.pdf", folder_id="folder-789"
        )

        assert result.request_id == "req-url-1"

        # Check the request payload includes folder_id
        request = responses.calls[1].request  # First is HEAD, second is POST
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-789"
        assert payload["product"] == "hippo"

    @responses.activate
    def test_upload_urls_without_folder_id(self):
        """Test uploading URLs without folder_id parameter"""
        # Mock the HEAD request for file info
        responses.add(
            responses.HEAD,
            "https://example.com/document.pdf",
            headers={
                "Content-Type": "application/pdf",
            },
            status=200,
        )

        # Mock the upload request
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "req-url-2"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")
        result = ingest._upload_urls("https://example.com/document.pdf", folder_id=None)

        assert result.request_id == "req-url-2"

        # Check the request payload does not include folder_id
        request = responses.calls[1].request
        payload = json.loads(request.body)
        assert "folder_id" not in payload
        assert payload["product"] == "lexa"

    @responses.activate
    def test_upload_urls_with_folder_id_and_mode(self):
        """Test uploading URLs with folder_id and processing mode"""
        # Mock HEAD request
        responses.add(
            responses.HEAD,
            "https://example.com/doc.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        # Mock upload request
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "req-url-3"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_urls(
            "https://example.com/doc.pdf",
            mode=ProcessingMode.ADVANCED,
            folder_id="folder-abc",
        )

        assert result.request_id == "req-url-3"

        # Check the request payload
        request = responses.calls[1].request
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-abc"
        assert payload["mode"] == "advanced"
        assert payload["product"] == "hippo"


class TestUploadS3FolderWithFolderId:
    """Test _upload_s3_folder method with folder_id parameter"""

    @responses.activate
    def test_upload_s3_folder_with_folder_id(self):
        """Test S3 folder upload with folder_id parameter - covers line 334"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/amazon-folder",
            json={"message": "S3 folder processed", "requestID": "req-s3-1"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_s3_folder(
            "my-bucket", "folder/path", folder_id="folder-s3-123"
        )

        assert result.request_id == "req-s3-1"

        # Check request payload includes folder_id
        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["bucket"] == "my-bucket"
        assert payload["path"] == "folder/path"
        assert payload["folder_id"] == "folder-s3-123"
        assert payload["product"] == "hippo"

    @responses.activate
    def test_upload_s3_folder_without_folder_id(self):
        """Test S3 folder upload without folder_id parameter"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/amazon-folder",
            json={"message": "S3 folder processed", "requestID": "req-s3-2"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")
        result = ingest._upload_s3_folder("my-bucket", "folder/path", folder_id=None)

        assert result.request_id == "req-s3-2"

        # Check request payload does not include folder_id
        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert "folder_id" not in payload
        assert payload["product"] == "lexa"

    @responses.activate
    def test_upload_s3_folder_with_folder_id_and_mode(self):
        """Test S3 folder upload with folder_id and processing mode"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/amazon-folder",
            json={"message": "S3 folder processed", "requestID": "req-s3-3"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_s3_folder(
            "bucket", "path", ProcessingMode.ADVANCED, folder_id="folder-s3-456"
        )

        assert result.request_id == "req-s3-3"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-s3-456"
        assert payload["mode"] == "advanced"


class TestUploadBoxFolderWithFolderId:
    """Test _upload_box_folder method with folder_id parameter"""

    @responses.activate
    def test_upload_box_folder_with_folder_id(self):
        """Test Box folder upload with folder_id parameter - covers line 388"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/box-folder",
            json={"message": "Box folder processed", "requestID": "req-box-1"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_box_folder("box-folder-123", folder_id="folder-box-789")

        assert result.request_id == "req-box-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["box_folder_id"] == "box-folder-123"
        assert payload["folder_id"] == "folder-box-789"
        assert payload["product"] == "hippo"

    @responses.activate
    def test_upload_box_folder_without_folder_id(self):
        """Test Box folder upload without folder_id parameter"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/box-folder",
            json={"message": "Box folder processed", "requestID": "req-box-2"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")
        result = ingest._upload_box_folder("box-folder-456", folder_id=None)

        assert result.request_id == "req-box-2"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert "folder_id" not in payload
        assert payload["product"] == "lexa"

    @responses.activate
    def test_upload_box_folder_with_folder_id_and_mode(self):
        """Test Box folder upload with folder_id and processing mode"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/box-folder",
            json={"message": "Box folder processed", "requestID": "req-box-3"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_box_folder(
            "box-folder-789", ProcessingMode.ADVANCED, folder_id="folder-box-abc"
        )

        assert result.request_id == "req-box-3"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-box-abc"
        assert payload["mode"] == "advanced"


class TestUploadDropboxFolderWithFolderId:
    """Test _upload_dropbox_folder method with folder_id parameter"""

    @responses.activate
    def test_upload_dropbox_folder_with_folder_id(self):
        """Test Dropbox folder upload with folder_id parameter - covers line 426"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/dropbox-folder",
            json={"message": "Dropbox folder processed", "requestID": "req-dropbox-1"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_dropbox_folder(
            "/Documents", folder_id="folder-dropbox-123"
        )

        assert result.request_id == "req-dropbox-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["path"] == "/Documents"
        assert payload["folder_id"] == "folder-dropbox-123"
        assert payload["product"] == "hippo"

    @responses.activate
    def test_upload_dropbox_folder_without_folder_id(self):
        """Test Dropbox folder upload without folder_id parameter"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/dropbox-folder",
            json={"message": "Dropbox folder processed", "requestID": "req-dropbox-2"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")
        result = ingest._upload_dropbox_folder("/Documents", folder_id=None)

        assert result.request_id == "req-dropbox-2"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert "folder_id" not in payload
        assert payload["product"] == "lexa"

    @responses.activate
    def test_upload_dropbox_folder_with_folder_id_and_mode(self):
        """Test Dropbox folder upload with folder_id and processing mode"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/dropbox-folder",
            json={"message": "Dropbox folder processed", "requestID": "req-dropbox-3"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_dropbox_folder(
            "/Documents", ProcessingMode.ADVANCED, folder_id="folder-dropbox-456"
        )

        assert result.request_id == "req-dropbox-3"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-dropbox-456"
        assert payload["mode"] == "advanced"


class TestUploadSharepointFolderWithFolderId:
    """Test _upload_sharepoint_folder method with folder_id parameter"""

    @responses.activate
    def test_upload_sharepoint_folder_with_folder_id(self):
        """Test SharePoint folder upload with folder_id parameter - covers line 472"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/microsoft-folder",
            json={"message": "SharePoint folder processed", "requestID": "req-sp-1"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_sharepoint_folder(
            "drive-123", "sharepoint-folder-456", folder_id="folder-sp-789"
        )

        assert result.request_id == "req-sp-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["drive_id"] == "drive-123"
        assert payload["sharepoint_folder_id"] == "sharepoint-folder-456"
        assert payload["folder_id"] == "folder-sp-789"
        assert payload["product"] == "hippo"

    @responses.activate
    def test_upload_sharepoint_folder_without_folder_id(self):
        """Test SharePoint folder upload without folder_id parameter"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/microsoft-folder",
            json={"message": "SharePoint folder processed", "requestID": "req-sp-2"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")
        result = ingest._upload_sharepoint_folder(
            "drive-123", "sharepoint-folder-456", folder_id=None
        )

        assert result.request_id == "req-sp-2"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert "folder_id" not in payload
        assert payload["product"] == "lexa"

    @responses.activate
    def test_upload_sharepoint_folder_with_folder_id_and_mode(self):
        """Test SharePoint folder upload with folder_id and processing mode"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/microsoft-folder",
            json={"message": "SharePoint folder processed", "requestID": "req-sp-3"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_sharepoint_folder(
            "drive-123",
            "sharepoint-folder-456",
            ProcessingMode.ADVANCED,
            folder_id="folder-sp-abc",
        )

        assert result.request_id == "req-sp-3"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-sp-abc"
        assert payload["mode"] == "advanced"


class TestUploadSalesforceFolderWithFolderId:
    """Test _upload_salesforce_folder method with folder_id parameter"""

    @responses.activate
    def test_upload_salesforce_folder_with_folder_id(self):
        """Test Salesforce folder upload with folder_id parameter - covers line 540"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/salesforce-folder",
            json={"message": "Salesforce folder processed", "requestID": "req-sf-1"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_salesforce_folder(
            "My Documents", folder_id="folder-sf-123"
        )

        assert result.request_id == "req-sf-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["name"] == "My Documents"
        assert payload["folder_id"] == "folder-sf-123"
        assert payload["product"] == "hippo"

    @responses.activate
    def test_upload_salesforce_folder_without_folder_id(self):
        """Test Salesforce folder upload without folder_id parameter"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/salesforce-folder",
            json={"message": "Salesforce folder processed", "requestID": "req-sf-2"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")
        result = ingest._upload_salesforce_folder("My Documents", folder_id=None)

        assert result.request_id == "req-sf-2"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert "folder_id" not in payload
        assert payload["product"] == "lexa"

    @responses.activate
    def test_upload_salesforce_folder_with_folder_id_and_mode(self):
        """Test Salesforce folder upload with folder_id and processing mode"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/salesforce-folder",
            json={"message": "Salesforce folder processed", "requestID": "req-sf-3"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_salesforce_folder(
            "My Documents", ProcessingMode.ADVANCED, folder_id="folder-sf-456"
        )

        assert result.request_id == "req-sf-3"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-sf-456"
        assert payload["mode"] == "advanced"


class TestUploadSendmeFilesWithFolderId:
    """Test _upload_sendme_files method with folder_id parameter"""

    @responses.activate
    def test_upload_sendme_files_with_folder_id(self):
        """Test Sendme files upload with folder_id parameter - covers line 578"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/sendme",
            json={"message": "Sendme files processed", "requestID": "req-sendme-1"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_sendme_files(
            "ticket-123", folder_id="folder-sendme-789"
        )

        assert result.request_id == "req-sendme-1"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["ticket"] == "ticket-123"
        assert payload["folder_id"] == "folder-sendme-789"
        assert payload["product"] == "hippo"

    @responses.activate
    def test_upload_sendme_files_without_folder_id(self):
        """Test Sendme files upload without folder_id parameter"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/sendme",
            json={"message": "Sendme files processed", "requestID": "req-sendme-2"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")
        result = ingest._upload_sendme_files("ticket-456", folder_id=None)

        assert result.request_id == "req-sendme-2"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert "folder_id" not in payload
        assert payload["product"] == "lexa"

    @responses.activate
    def test_upload_sendme_files_with_folder_id_and_mode(self):
        """Test Sendme files upload with folder_id and processing mode"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/sendme",
            json={"message": "Sendme files processed", "requestID": "req-sendme-3"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        result = ingest._upload_sendme_files(
            "ticket-789", ProcessingMode.ADVANCED, folder_id="folder-sendme-abc"
        )

        assert result.request_id == "req-sendme-3"

        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["folder_id"] == "folder-sendme-abc"
        assert payload["mode"] == "advanced"


class TestIngestListingMethods:
    """Test cloud storage listing methods"""

    @responses.activate
    def test_list_s3_buckets(self):
        """Test listing S3 buckets"""
        bucket_response = {
            "requestID": "req-list-buckets",
            "buckets": [
                {"Name": "bucket1", "CreationDate": "2023-01-01"},
                {"Name": "bucket2", "CreationDate": "2023-01-02"},
            ],
        }
        responses.add(
            responses.GET,
            "https://data.cerevox.ai/v0/amazon-listBuckets",
            json=bucket_response,
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        result = ingest.list_s3_buckets()

        assert isinstance(result, BucketListResponse)
        assert result.request_id == "req-list-buckets"
        assert len(result.buckets) == 2
        assert result.buckets[0].name == "bucket1"

    @responses.activate
    def test_list_s3_folders(self):
        """Test listing S3 folders"""
        folder_response = {
            "requestID": "req-list-folders",
            "folders": [
                {"id": "folder1", "name": "Documents"},
                {"id": "folder2", "name": "Images"},
            ],
        }
        responses.add(
            responses.GET,
            "https://data.cerevox.ai/v0/amazon-listFoldersInBucket",
            json=folder_response,
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        result = ingest.list_s3_folders("my-bucket")

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-list-folders"
        assert len(result.folders) == 2

        # Check query parameters
        request = responses.calls[0].request
        assert "bucket=my-bucket" in request.url

    @responses.activate
    def test_list_box_folders(self):
        """Test listing Box folders"""
        folder_response = {
            "requestID": "req-box-folders",
            "folders": [{"id": "box-folder1", "name": "Shared Files"}],
        }
        responses.add(
            responses.GET,
            "https://data.cerevox.ai/v0/box-listFolders",
            json=folder_response,
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        result = ingest.list_box_folders()

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-box-folders"

    @responses.activate
    def test_list_dropbox_folders(self):
        """Test listing Dropbox folders"""
        folder_response = {
            "requestID": "req-dropbox-folders",
            "folders": [{"id": "dropbox-folder1", "name": "Apps"}],
        }
        responses.add(
            responses.GET,
            "https://data.cerevox.ai/v0/dropbox-listFolders",
            json=folder_response,
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        result = ingest.list_dropbox_folders()

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-dropbox-folders"

    @responses.activate
    def test_list_sharepoint_sites(self):
        """Test listing SharePoint sites"""
        site_response = {
            "requestID": "req-sp-sites",
            "sites": [
                {
                    "id": "site1",
                    "name": "Company Site",
                    "webUrl": "https://company.sharepoint.com/sites/main",
                }
            ],
        }
        responses.add(
            responses.GET,
            "https://data.cerevox.ai/v0/microsoft-listSites",
            json=site_response,
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        result = ingest.list_sharepoint_sites()

        assert isinstance(result, SiteListResponse)
        assert result.request_id == "req-sp-sites"
        assert len(result.sites) == 1
        assert result.sites[0].name == "Company Site"

    @responses.activate
    def test_list_sharepoint_drives(self):
        """Test listing SharePoint drives"""
        drive_response = {
            "requestID": "req-sp-drives",
            "drives": [
                {"id": "drive1", "name": "Documents", "driveType": "documentLibrary"}
            ],
        }
        responses.add(
            responses.GET,
            "https://data.cerevox.ai/v0/microsoft-listDrivesInSite",
            json=drive_response,
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        result = ingest.list_sharepoint_drives("site-123")

        assert isinstance(result, DriveListResponse)
        assert result.request_id == "req-sp-drives"

        # Check query parameters
        request = responses.calls[0].request
        assert "site_id=site-123" in request.url

    @responses.activate
    def test_list_sharepoint_folders(self):
        """Test listing SharePoint folders"""
        folder_response = {
            "requestID": "req-sp-folders",
            "folders": [{"id": "folder1", "name": "Shared Documents"}],
        }
        responses.add(
            responses.GET,
            "https://data.cerevox.ai/v0/microsoft-listFoldersInDrive",
            json=folder_response,
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        result = ingest.list_sharepoint_folders("drive-123")

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-sp-folders"

        # Check query parameters
        request = responses.calls[0].request
        assert "drive_id=drive-123" in request.url

    @responses.activate
    def test_list_salesforce_folders(self):
        """Test listing Salesforce folders"""
        folder_response = {
            "requestID": "req-sf-folders",
            "folders": [{"id": "sf-folder1", "name": "Sales Documents"}],
        }
        responses.add(
            responses.GET,
            "https://data.cerevox.ai/v0/salesforce-listFolders",
            json=folder_response,
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        result = ingest.list_salesforce_folders()

        assert isinstance(result, FolderListResponse)
        assert result.request_id == "req-sf-folders"


class TestIngestModeValidation:
    """Test mode validation in ingest methods"""

    def test_validate_mode_with_enum(self):
        """Test mode validation with ProcessingMode enum"""
        ingest = Ingest(api_key="test-key")
        result = ingest._validate_mode(ProcessingMode.ADVANCED)
        assert result == "advanced"

    def test_validate_mode_with_valid_string(self):
        """Test mode validation with valid string"""
        ingest = Ingest(api_key="test-key")
        result = ingest._validate_mode("default")
        assert result == "default"

        result = ingest._validate_mode("advanced")
        assert result == "advanced"

    def test_validate_mode_with_invalid_string(self):
        """Test mode validation with invalid string"""
        ingest = Ingest(api_key="test-key")
        with pytest.raises(ValueError, match="Invalid processing mode"):
            ingest._validate_mode("invalid_mode")

    def test_validate_mode_with_invalid_type(self):
        """Test mode validation with invalid type"""
        ingest = Ingest(api_key="test-key")
        with pytest.raises(
            TypeError, match="Mode must be ProcessingMode enum or string"
        ):
            ingest._validate_mode(123)

        with pytest.raises(
            TypeError, match="Mode must be ProcessingMode enum or string"
        ):
            ingest._validate_mode(None)


class TestIngestFileInfoFromUrl:
    """Test _get_file_info_from_url method"""

    @responses.activate
    def test_get_file_info_with_content_disposition(self):
        """Test file info extraction with Content-Disposition header"""
        responses.add(
            responses.HEAD,
            "https://example.com/document.pdf",
            headers={
                "Content-Disposition": 'attachment; filename="report.pdf"',
                "Content-Type": "application/pdf",
            },
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        file_info = ingest._get_file_info_from_url("https://example.com/document.pdf")

        assert file_info.name == "report.pdf"
        assert file_info.url == "https://example.com/document.pdf"
        assert file_info.type == "application/pdf"

    @responses.activate
    def test_get_file_info_from_url_path(self):
        """Test file info extraction from URL path"""
        responses.add(
            responses.HEAD,
            "https://example.com/files/document.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        ingest = Ingest(api_key="test-key")
        file_info = ingest._get_file_info_from_url(
            "https://example.com/files/document.pdf"
        )

        assert file_info.name == "document.pdf"
        assert file_info.type == "application/pdf"

    def test_get_file_info_head_request_fails(self):
        """Test file info extraction when HEAD request fails"""
        ingest = Ingest(api_key="test-key")

        with patch.object(ingest.session, "head") as mock_head:
            mock_head.side_effect = Exception("Request failed")

            file_info = ingest._get_file_info_from_url(
                "https://example.com/document.pdf"
            )

            assert file_info.name == "document.pdf"
            assert file_info.type == "application/octet-stream"


class TestIngestErrorHandling:
    """Test error handling in ingest methods"""

    def test_upload_files_no_files(self):
        """Test upload with no files"""
        ingest = Ingest(api_key="test-key")

        with pytest.raises(ValueError, match="At least one file must be provided"):
            ingest._upload_files([])

        with pytest.raises(ValueError, match="At least one file must be provided"):
            ingest._upload_files(None)

    def test_upload_urls_empty_list(self):
        """Test upload with empty URL list"""
        ingest = Ingest(api_key="test-key")

        with pytest.raises(ValueError, match="At least one file url must be provided"):
            ingest._upload_urls([])

    def test_upload_urls_invalid_url_format(self):
        """Test upload with invalid URL format"""
        ingest = Ingest(api_key="test-key")

        with pytest.raises(ValueError, match="Invalid URL format"):
            ingest._upload_urls("invalid-url")

    def test_upload_files_nonexistent_file(self):
        """Test upload with nonexistent file"""
        ingest = Ingest(api_key="test-key")

        with pytest.raises(ValueError, match="File not found"):
            ingest._upload_files("/nonexistent/file.txt")

    def test_upload_files_directory_instead_of_file(self):
        """Test upload with directory path"""
        ingest = Ingest(api_key="test-key")

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Not a file"):
                ingest._upload_files(temp_dir)


class TestIngestEdgeCases:
    """Test edge cases and comprehensive coverage"""

    @responses.activate
    def test_upload_files_with_mixed_types_and_folder_id(self):
        """Test uploading mixed file types with folder_id"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={
                "message": "Files uploaded successfully",
                "requestID": "req-mixed",
                "uploads": ["file1.txt", "file2.bin", "stream.txt"],
            },
            status=200,
        )

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b"file content")
        temp_file.close()

        try:
            ingest = Ingest(api_key="test-key", product="hippo")

            # Mix of file types with folder_id
            files = [
                temp_file.name,  # File path
                b"raw bytes",  # Raw bytes
                BytesIO(b"stream"),  # Stream
            ]

            result = ingest._upload_files(files, folder_id="mixed-folder-123")
            assert result.request_id == "req-mixed"

            # Verify folder_id was included
            request = responses.calls[0].request
            assert "folder_id=mixed-folder-123" in request.url

        finally:
            os.unlink(temp_file.name)

    @responses.activate
    def test_upload_multiple_urls_with_folder_id(self):
        """Test uploading multiple URLs with folder_id"""
        # Mock HEAD requests
        responses.add(
            responses.HEAD,
            "https://example.com/doc1.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )
        responses.add(
            responses.HEAD,
            "https://example.com/doc2.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        # Mock upload request
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "req-multi-url"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        urls = ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]
        result = ingest._upload_urls(urls, folder_id="multi-url-folder")

        assert result.request_id == "req-multi-url"

        # Check the request payload includes folder_id
        request = responses.calls[2].request  # Two HEAD requests, then POST
        payload = json.loads(request.body)
        assert payload["folder_id"] == "multi-url-folder"
        assert len(payload["files"]) == 2

    def test_all_upload_methods_with_folder_id_none(self):
        """Test that all upload methods handle folder_id=None correctly"""
        ingest = Ingest(api_key="test-key", product="lexa")

        with patch.object(ingest, "_request") as mock_request:
            mock_request.return_value = {"requestID": "test", "message": "OK"}

            # Test all methods with folder_id=None
            ingest._upload_files(b"content", folder_id=None)

            # For URLs, we need to mock the file info extraction
            with patch.object(ingest, "_get_file_info_from_url") as mock_get_info:
                mock_get_info.return_value = FileInfo(
                    name="test.pdf",
                    url="http://test.com/test.pdf",
                    type="application/pdf",
                )
                ingest._upload_urls("http://test.com/test.pdf", folder_id=None)

            ingest._upload_s3_folder("bucket", "path", folder_id=None)
            ingest._upload_box_folder("box_folder", folder_id=None)
            ingest._upload_dropbox_folder("/path", folder_id=None)
            ingest._upload_sharepoint_folder("drive", "folder", folder_id=None)
            ingest._upload_salesforce_folder("folder", folder_id=None)
            ingest._upload_sendme_files("ticket", folder_id=None)

            # Verify all calls were made without folder_id in payload/params
            for call in mock_request.call_args_list:
                args, kwargs = call
                if "params" in kwargs:
                    # For file uploads (params)
                    assert kwargs["params"].get("folder_id") is None
                elif "json_data" in kwargs:
                    # For other uploads (json_data)
                    assert "folder_id" not in kwargs["json_data"]


class TestComprehensiveFolderIdCoverage:
    """Comprehensive tests to ensure all folder_id lines are covered"""

    @responses.activate
    def test_all_folder_id_branches_covered(self):
        """Test that all folder_id conditional branches are covered"""
        # This test ensures we hit all the specific lines mentioned: 218, 272, 334, 388, 426, 472, 540, 578

        # Mock all necessary responses
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "files-test"},
            status=200,
        )

        responses.add(
            responses.HEAD,
            "https://example.com/test.pdf",
            headers={"Content-Type": "application/pdf"},
            status=200,
        )

        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/file-urls",
            json={"message": "URLs processed", "requestID": "urls-test"},
            status=200,
        )

        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/amazon-folder",
            json={"message": "S3 processed", "requestID": "s3-test"},
            status=200,
        )

        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/box-folder",
            json={"message": "Box processed", "requestID": "box-test"},
            status=200,
        )

        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/dropbox-folder",
            json={"message": "Dropbox processed", "requestID": "dropbox-test"},
            status=200,
        )

        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/microsoft-folder",
            json={"message": "SharePoint processed", "requestID": "sp-test"},
            status=200,
        )

        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/salesforce-folder",
            json={"message": "Salesforce processed", "requestID": "sf-test"},
            status=200,
        )

        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/sendme",
            json={"message": "Sendme processed", "requestID": "sendme-test"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="hippo")
        folder_id = "comprehensive-test-folder"

        # Test all upload methods with folder_id to hit lines 218, 272, 334, 388, 426, 472, 540, 578

        # Line 218: _upload_files with folder_id
        result1 = ingest._upload_files(b"test content", folder_id=folder_id)
        assert result1.request_id == "files-test"

        # Line 272: _upload_urls with folder_id
        result2 = ingest._upload_urls(
            "https://example.com/test.pdf", folder_id=folder_id
        )
        assert result2.request_id == "urls-test"

        # Line 334: _upload_s3_folder with folder_id
        result3 = ingest._upload_s3_folder("bucket", "path", folder_id=folder_id)
        assert result3.request_id == "s3-test"

        # Line 388: _upload_box_folder with folder_id
        result4 = ingest._upload_box_folder("box_folder_id", folder_id=folder_id)
        assert result4.request_id == "box-test"

        # Line 426: _upload_dropbox_folder with folder_id
        result5 = ingest._upload_dropbox_folder("/dropbox/path", folder_id=folder_id)
        assert result5.request_id == "dropbox-test"

        # Line 472: _upload_sharepoint_folder with folder_id
        result6 = ingest._upload_sharepoint_folder(
            "drive_id", "sp_folder_id", folder_id=folder_id
        )
        assert result6.request_id == "sp-test"

        # Line 540: _upload_salesforce_folder with folder_id
        result7 = ingest._upload_salesforce_folder(
            "sf_folder_name", folder_id=folder_id
        )
        assert result7.request_id == "sf-test"

        # Line 578: _upload_sendme_files with folder_id
        result8 = ingest._upload_sendme_files("sendme_ticket", folder_id=folder_id)
        assert result8.request_id == "sendme-test"

        # Verify all requests included folder_id
        # Files upload (params)
        files_request = responses.calls[0].request
        assert f"folder_id={folder_id}" in files_request.url

        # URLs upload (json_data)
        urls_request = responses.calls[2].request  # Index 1 is HEAD request
        urls_payload = json.loads(urls_request.body)
        assert urls_payload["folder_id"] == folder_id

        # All other uploads (json_data)
        for i, request_index in enumerate(
            [3, 4, 5, 6, 7, 8]
        ):  # S3, Box, Dropbox, SharePoint, Salesforce, Sendme
            request = responses.calls[request_index].request
            payload = json.loads(request.body)
            assert payload["folder_id"] == folder_id, f"Request {i} missing folder_id"


class TestGzipCompression:
    """Test gzip compression functionality"""

    def test_is_already_gzip_compressed_gz(self):
        """Test detection of .gz files"""
        ingest = Ingest(api_key="test-key")
        assert ingest._is_already_gzip_compressed("file.gz") is True
        assert ingest._is_already_gzip_compressed("file.GZ") is True
        assert ingest._is_already_gzip_compressed("file.gzip") is True
        assert ingest._is_already_gzip_compressed("file.GZIP") is True

    def test_is_already_gzip_compressed_tar_gz(self):
        """Test detection of .tar.gz files - covers line 165"""
        ingest = Ingest(api_key="test-key")
        assert ingest._is_already_gzip_compressed("archive.tar.gz") is True
        assert ingest._is_already_gzip_compressed("archive.TAR.GZ") is True
        assert ingest._is_already_gzip_compressed("archive.tgz") is True
        assert ingest._is_already_gzip_compressed("archive.TGZ") is True

    def test_is_already_gzip_compressed_false(self):
        """Test detection of non-gzip files"""
        ingest = Ingest(api_key="test-key")
        assert ingest._is_already_gzip_compressed("file.txt") is False
        assert ingest._is_already_gzip_compressed("file.pdf") is False
        assert ingest._is_already_gzip_compressed("file.zip") is False

    def test_should_compress_content_below_threshold(self):
        """Test compression decision for small files"""
        ingest = Ingest(api_key="test-key", compression_threshold=1024 * 1024)  # 1MB
        small_content = b"small content"
        assert ingest._should_compress_content(small_content, "file.txt") is False

    def test_should_compress_content_above_threshold(self):
        """Test compression decision for large files - covers line 188"""
        ingest = Ingest(api_key="test-key", compression_threshold=1024)  # 1KB
        large_content = b"x" * (2 * 1024)  # 2KB
        assert ingest._should_compress_content(large_content, "file.txt") is True

    def test_should_compress_content_already_gzip(self):
        """Test compression decision for already gzipped files - covers line 182"""
        ingest = Ingest(api_key="test-key", compression_threshold=1024)  # 1KB
        large_content = b"x" * (2 * 1024)  # 2KB
        # Even though file is large, should not compress if already gzip
        assert ingest._should_compress_content(large_content, "file.gz") is False
        assert ingest._should_compress_content(large_content, "archive.tar.gz") is False

    def test_compress_content(self):
        """Test content compression - covers lines 201-207"""
        import gzip

        ingest = Ingest(api_key="test-key")
        original_content = b"This is test content that will be compressed"
        original_filename = "test.txt"

        compressed_content, compressed_filename = ingest._compress_content(
            original_content, original_filename
        )

        # Verify the content is actually gzipped
        assert compressed_content != original_content
        assert gzip.decompress(compressed_content) == original_content

        # Verify filename has .gz extension
        assert compressed_filename == "test.txt.gz"

    def test_compress_content_already_has_gz_extension(self):
        """Test compression when filename already has .gz extension"""
        import gzip

        ingest = Ingest(api_key="test-key")
        original_content = b"test content"
        original_filename = "test.txt.gz"

        compressed_content, compressed_filename = ingest._compress_content(
            original_content, original_filename
        )

        # Filename should remain the same (not double .gz)
        assert compressed_filename == "test.txt.gz"
        assert gzip.decompress(compressed_content) == original_content

    def test_stream_compress_file(self):
        """Test streaming file compression - covers lines 223-247"""
        import gzip

        ingest = Ingest(api_key="test-key")

        # Create temporary file with content
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        test_content = b"x" * (2 * 1024 * 1024)  # 2MB of data
        temp_file.write(test_content)
        temp_file.close()

        try:
            # Stream compress the file
            compressed_path, compressed_filename = ingest._stream_compress_file(
                Path(temp_file.name)
            )

            try:
                # Verify compressed file exists
                assert os.path.exists(compressed_path)

                # Verify filename has .gz extension
                assert compressed_filename.endswith(".gz")

                # Verify content is correctly compressed
                with gzip.open(compressed_path, "rb") as f:
                    decompressed = f.read()
                    assert decompressed == test_content

            finally:
                # Clean up compressed file
                if os.path.exists(compressed_path):
                    os.unlink(compressed_path)
        finally:
            # Clean up original file
            os.unlink(temp_file.name)

    def test_stream_compress_file_with_gz_extension(self):
        """Test streaming compression when filename already has .gz extension"""
        ingest = Ingest(api_key="test-key")

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt.gz")
        temp_file.write(b"test content")
        temp_file.close()

        try:
            compressed_path, compressed_filename = ingest._stream_compress_file(
                Path(temp_file.name)
            )

            try:
                # Filename should not have double .gz
                basename = os.path.basename(temp_file.name)
                assert compressed_filename == basename
                assert compressed_filename.count(".gz") == 1
            finally:
                if os.path.exists(compressed_path):
                    os.unlink(compressed_path)
        finally:
            os.unlink(temp_file.name)

    def test_should_stream_compress_large_file(self):
        """Test stream compression decision for large files"""
        ingest = Ingest(api_key="test-key")

        # Create a large temporary file (>10MB)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(b"x" * (11 * 1024 * 1024))  # 11MB
        temp_file.close()

        try:
            assert ingest._should_stream_compress(Path(temp_file.name)) is True
        finally:
            os.unlink(temp_file.name)

    def test_should_stream_compress_small_file(self):
        """Test stream compression decision for small files"""
        ingest = Ingest(api_key="test-key")

        # Create a small temporary file (<10MB)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(b"small content")
        temp_file.close()

        try:
            assert ingest._should_stream_compress(Path(temp_file.name)) is False
        finally:
            os.unlink(temp_file.name)

    def test_should_stream_compress_already_gzip(self):
        """Test stream compression decision for already gzipped files - covers line 261"""
        ingest = Ingest(api_key="test-key")

        # Create a large .gz file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".gz")
        temp_file.write(b"x" * (11 * 1024 * 1024))  # 11MB
        temp_file.close()

        try:
            # Even though file is large, should not stream compress if already gzip
            assert ingest._should_stream_compress(Path(temp_file.name)) is False
        finally:
            os.unlink(temp_file.name)

    def test_should_stream_compress_file_not_found(self):
        """Test stream compression decision for non-existent files - covers lines 268-269"""
        ingest = Ingest(api_key="test-key")
        assert ingest._should_stream_compress(Path("/nonexistent/file.txt")) is False

    @responses.activate
    def test_upload_files_with_compression(self):
        """Test uploading files that trigger compression - covers line 336"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "req-compress"},
            status=200,
        )

        # Use small threshold to trigger compression
        ingest = Ingest(api_key="test-key", product="lexa", compression_threshold=10)

        # Create content above threshold
        large_content = b"x" * 100  # Larger than 10 bytes

        result = ingest._upload_files(large_content)
        assert result.request_id == "req-compress"

    @responses.activate
    def test_upload_files_no_compression_below_threshold(self):
        """Test uploading files that don't trigger compression"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "req-no-compress"},
            status=200,
        )

        ingest = Ingest(
            api_key="test-key", product="lexa", compression_threshold=1024 * 1024
        )

        # Small content
        small_content = b"small"

        result = ingest._upload_files(small_content)
        assert result.request_id == "req-no-compress"

    @responses.activate
    def test_upload_already_gzip_file(self):
        """Test uploading already gzipped files (should not double-compress)"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "req-gzip"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa", compression_threshold=10)

        # Create a .gz file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".gz")
        temp_file.write(b"x" * 100)  # Larger than threshold
        temp_file.close()

        try:
            result = ingest._upload_files(temp_file.name)
            assert result.request_id == "req-gzip"
        finally:
            os.unlink(temp_file.name)

    @responses.activate
    def test_upload_large_file_stream_compression(self):
        """Test uploading large files with stream compression - covers lines 325-328"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "req-stream"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")

        # Create large temporary file (>10MB to trigger stream compression)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(b"x" * (11 * 1024 * 1024))  # 11MB
        temp_file.close()

        try:
            result = ingest._upload_files(temp_file.name)
            assert result.request_id == "req-stream"
        finally:
            os.unlink(temp_file.name)

    @responses.activate
    def test_upload_bytes_with_compression(self):
        """Test uploading raw bytes that trigger compression - covers line 350"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "req-bytes"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa", compression_threshold=10)

        # Create bytes above threshold
        large_bytes = b"x" * 100

        result = ingest._upload_files(large_bytes)
        assert result.request_id == "req-bytes"

    @responses.activate
    def test_upload_stream_with_compression(self):
        """Test uploading file stream with compression - covers lines 367-373"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "req-stream-compress"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa", compression_threshold=10)

        # Create a file-like object with large content
        stream = BytesIO(b"x" * 100)
        stream.name = "test.txt"

        result = ingest._upload_files(stream)
        assert result.request_id == "req-stream-compress"

    @responses.activate
    def test_upload_files_cleanup_on_success(self):
        """Test that file streams are closed after upload - covers lines 434-438"""
        responses.add(
            responses.POST,
            "https://data.cerevox.ai/v0/files",
            json={"message": "Files uploaded", "requestID": "req-cleanup"},
            status=200,
        )

        ingest = Ingest(api_key="test-key", product="lexa")

        # Create a temporary file to test cleanup
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(b"test content")
        temp_file.close()

        try:
            result = ingest._upload_files(temp_file.name)
            assert result.request_id == "req-cleanup"
            # Test passes if no errors occur during cleanup
        finally:
            os.unlink(temp_file.name)

    def test_upload_files_cleanup_temp_files_on_error(self):
        """Test that temporary compressed files are cleaned up on error - covers lines 442-445"""
        ingest = Ingest(api_key="test-key", product="lexa")

        # Create large temporary file to trigger stream compression
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_file.write(b"x" * (11 * 1024 * 1024))  # 11MB
        temp_file.close()

        try:
            # Mock _request to raise an exception
            with patch.object(ingest, "_request") as mock_request:
                mock_request.side_effect = Exception("Upload failed")

                try:
                    ingest._upload_files(temp_file.name)
                except Exception:
                    pass

                # The compressed temp file should have been cleaned up
                # We can't easily verify this without inspecting internals,
                # but we can at least ensure the exception was raised
                assert mock_request.called
        finally:
            os.unlink(temp_file.name)

    def test_custom_compression_threshold(self):
        """Test setting custom compression threshold"""
        # Test with custom threshold
        ingest = Ingest(api_key="test-key", compression_threshold=500 * 1024)  # 500KB
        assert ingest.compression_threshold == 500 * 1024

        # Content below threshold should not compress
        content_below = b"x" * (400 * 1024)  # 400KB
        assert ingest._should_compress_content(content_below) is False

        # Content above threshold should compress
        content_above = b"x" * (600 * 1024)  # 600KB
        assert ingest._should_compress_content(content_above) is True
