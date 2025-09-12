"""
Test suite for cerevox.apis.hippo

Comprehensive tests to achieve 100% code coverage for the Hippo class,
including all methods, error handling, and edge cases.
"""

import json
import os
from unittest.mock import Mock, mock_open, patch

import pytest
import responses
from requests.exceptions import ConnectionError, RequestException, Timeout

from cerevox import Hippo
from cerevox.core import (
    AskItem,
    AskListItem,
    AsksListResponse,
    AskSubmitResponse,
    ChatCreatedResponse,
    ChatItem,
    DeletedResponse,
    FileItem,
    FileUploadResponse,
    FolderCreatedResponse,
    FolderItem,
    IngestionResult,
    LexaAuthError,
    LexaError,
    LexaTimeoutError,
    MessageResponse,
    ProcessingMode,
    TokenResponse,
    UpdatedResponse,
)


class TestHippoInitialization:
    """Test Hippo client initialization"""

    def test_init_with_api_key(self):
        """Test initialization with API key parameter"""
        with responses.RequestsMock() as rsps:
            # Mock login response
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )

            client = Hippo(api_key="test-api-key")
            assert client.api_key == "test-api-key"
            assert client.data_url == "https://dev.cerevox.ai/v1"
            assert client.timeout == 30.0
            assert client.max_retries == 3
            assert "Authorization" in client.session.headers

    def test_init_with_env_api_key(self):
        """Test initialization with API key from environment"""
        with patch.dict(os.environ, {"CEREVOX_API_KEY": "env-api-key"}):
            with responses.RequestsMock() as rsps:
                rsps.add(
                    responses.POST,
                    "https://dev.cerevox.ai/v1/token/login",
                    json={
                        "access_token": "test-access-token",
                        "expires_in": 3600,
                        "refresh_token": "test-refresh-token",
                        "token_type": "Bearer",
                    },
                    status=200,
                )

                client = Hippo(api_key=None)
                assert client.api_key == "env-api-key"

    def test_init_missing_credentials(self):
        """Test initialization fails without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="api_key is required for authentication"
            ):
                Hippo(api_key=None)

    def test_init_invalid_data_url(self):
        """Test initialization with invalid base URL"""
        with pytest.raises(ValueError, match="data_url must start with"):
            Hippo(api_key="test-key", data_url="invalid-url")

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )

            session_kwargs = {"verify": False}
            client = Hippo(
                email="test@example.com",
                api_key="test-key",
                data_url="https://dev.cerevox.ai/v1",
                timeout=60.0,
                max_retries=5,
                session_kwargs=session_kwargs,
                custom_param="test",
            )

            assert client.data_url == "https://dev.cerevox.ai/v1"
            assert client.timeout == 60.0
            assert client.max_retries == 5
            assert not client.session.verify

    def test_context_manager(self):
        """Test context manager functionality"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )

            with Hippo(api_key="test-key") as client:
                assert client.session is not None

            # Session should be closed after context exit
            # Note: We can't easily test if session is closed without accessing private attributes


class TestHippoAuthentication:
    """Test authentication methods"""

    def setup_method(self):
        """Set up test client"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            self.client = Hippo(api_key="test-key")

    @responses.activate
    def test_login_success(self):
        """Test successful login"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/token/login",
            json={
                "access_token": "new-access-token",
                "expires_in": 3600,
                "refresh_token": "new-refresh-token",
                "token_type": "Bearer",
            },
            status=200,
        )

        response = self.client._login("test-api-key")

        assert isinstance(response, TokenResponse)
        assert response.access_token == "new-access-token"
        assert "Bearer new-access-token" in self.client.session.headers["Authorization"]

    @responses.activate
    def test_login_failure(self):
        """Test login failure"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/token/login",
            json={"error": "Invalid credentials"},
            status=401,
        )

        with pytest.raises(LexaAuthError):
            self.client._login("wrong-api-key")

    @responses.activate
    def test_refresh_token_success(self):
        """Test successful token refresh"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/token/refresh",
            json={
                "access_token": "refreshed-access-token",
                "expires_in": 3600,
                "refresh_token": "new-refresh-token",
                "token_type": "Bearer",
            },
            status=200,
        )

        response = self.client._refresh_token("old-refresh-token")

        assert isinstance(response, TokenResponse)
        assert response.access_token == "refreshed-access-token"
        assert (
            "Bearer refreshed-access-token"
            in self.client.session.headers["Authorization"]
        )

    @responses.activate
    def test_revoke_token_success(self):
        """Test successful token revocation"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/token/revoke",
            json={"message": "Token revoked successfully", "status": "ok"},
            status=200,
        )

        response = self.client._revoke_token()

        assert isinstance(response, MessageResponse)
        assert response.message == "Token revoked successfully"


class TestHippoFolderManagement:
    """Test folder management methods"""

    def setup_method(self):
        """Set up test client"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            self.client = Hippo(api_key="test-key")

    @responses.activate
    def test_create_folder_success(self):
        """Test successful folder creation"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/folders",
            json={
                "created": True,
                "status": "ok",
                "folder_id": "test-folder",
                "folder_name": "Test Folder",
            },
            status=200,
        )

        response = self.client.create_folder("test-folder", "Test Folder")

        assert isinstance(response, FolderCreatedResponse)
        assert response.created is True
        assert response.folder_id == "test-folder"
        assert response.folder_name == "Test Folder"

    @responses.activate
    def test_get_folders_success(self):
        """Test successful folder listing"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders",
            json={
                "folders": [
                    {"folder_id": "folder1", "folder_name": "Folder 1"},
                    {"folder_id": "folder2", "folder_name": "Folder 2"},
                ]
            },
            status=200,
        )

        response = self.client.get_folders()

        assert isinstance(response, list)
        assert len(response) == 2
        assert all(isinstance(folder, FolderItem) for folder in response)
        assert response[0].folder_id == "folder1"

    @responses.activate
    def test_get_folders_with_search(self):
        """Test folder listing with search parameter"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders",
            json={"folders": [{"folder_id": "folder1", "folder_name": "Test Folder"}]},
            status=200,
        )

        response = self.client.get_folders(search_name="test")

        assert len(response) == 1
        assert response[0].folder_name == "Test Folder"

    @responses.activate
    def test_get_folder_by_id_success(self):
        """Test successful folder retrieval by ID"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders/test-folder",
            json={
                "folder_id": "test-folder",
                "folder_name": "Test Folder",
                "status": "ready",
                "currentSize": 1024,
                "historicalSize": 2048,
            },
            status=200,
        )

        response = self.client.get_folder_by_id("test-folder")

        assert isinstance(response, FolderItem)
        assert response.folder_id == "test-folder"
        assert response.status == "ready"
        assert response.currentSize == 1024

    @responses.activate
    def test_update_folder_success(self):
        """Test successful folder update"""
        responses.add(
            responses.PUT,
            "https://dev.cerevox.ai/v1/folders/test-folder",
            json={"updated": True, "status": "ok"},
            status=200,
        )

        response = self.client.update_folder("test-folder", "Updated Folder Name")

        assert isinstance(response, UpdatedResponse)
        assert response.updated is True

    @responses.activate
    def test_delete_folder_success(self):
        """Test successful folder deletion"""
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/folders/test-folder",
            json={"deleted": True, "status": "ok"},
            status=200,
        )

        response = self.client.delete_folder("test-folder")

        assert isinstance(response, DeletedResponse)
        assert response.deleted is True


class TestHippoFileManagement:
    """Test file management methods"""

    def setup_method(self):
        """Set up test client"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            self.client = Hippo(api_key="test-key")

    def test_upload_file_success(self):
        """Test successful file upload"""
        # Mock the ingest service method instead of direct API call
        mock_result = IngestionResult(
            message="Files uploaded successfully",
            request_id="test-req-456",
            uploads=["test.txt"],
        )

        with patch.object(self.client, "_upload_files", return_value=mock_result):
            response = self.client.upload_file("test-folder", "/path/to/test.txt")

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-456"
        assert "test.txt" in response.uploads

    def test_upload_file_from_url_success(self):
        """Test successful file upload from URL"""
        # Mock the ingest service method instead of direct API call
        mock_result = IngestionResult(
            message="Files uploaded successfully",
            request_id="test-req-101",
            uploads=["remote-file.pdf"],
        )

        with patch.object(self.client, "_upload_urls", return_value=mock_result):
            files = ["https://example.com/file.pdf"]
            response = self.client.upload_file_from_url("test-folder", files)

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-101"
        assert "remote-file.pdf" in response.uploads

    @responses.activate
    def test_get_files_success(self):
        """Test successful file listing"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            json={
                "files": [
                    {
                        "file_id": "file1",
                        "name": "document1.pdf",
                        "size": 1024,
                        "type": "application/pdf",
                    }
                ]
            },
            status=200,
        )

        response = self.client.get_files("test-folder")

        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], FileItem)
        assert response[0].file_id == "file1"

    @responses.activate
    def test_get_files_with_search(self):
        """Test file listing with search parameter"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            json={
                "files": [
                    {
                        "file_id": "file1",
                        "name": "test-document.pdf",
                        "size": 1024,
                        "type": "application/pdf",
                    }
                ]
            },
            status=200,
        )

        response = self.client.get_files("test-folder", search_name="test")

        assert len(response) == 1
        assert response[0].name == "test-document.pdf"

    @responses.activate
    def test_get_file_by_id_success(self):
        """Test successful file retrieval by ID"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders/test-folder/files/file1",
            json={
                "file_id": "file1",
                "name": "document.pdf",
                "size": 2048,
                "type": "application/pdf",
                "provider": "local",
                "source": "upload",
            },
            status=200,
        )

        response = self.client.get_file_by_id("test-folder", "file1")

        assert isinstance(response, FileItem)
        assert response.file_id == "file1"
        assert response.size == 2048

    @responses.activate
    def test_delete_file_by_id_success(self):
        """Test successful file deletion by ID"""
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/folders/test-folder/files/file1",
            json={"deleted": True, "status": "ok"},
            status=200,
        )

        response = self.client.delete_file_by_id("test-folder", "file1")

        assert isinstance(response, DeletedResponse)
        assert response.deleted is True

    @responses.activate
    def test_delete_all_files_success(self):
        """Test successful deletion of all files"""
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            json={"deleted": True, "status": "ok"},
            status=200,
        )

        response = self.client.delete_all_files("test-folder")

        assert isinstance(response, DeletedResponse)
        assert response.deleted is True

    def test_upload_s3_folder_success(self):
        """Test successful S3 folder upload"""
        # Mock the ingest service method instead of direct API call
        mock_result = IngestionResult(
            message="S3 folder uploaded successfully",
            request_id="test-req-s3-123",
            uploads=["file1.pdf", "file2.docx"],
        )

        with patch.object(self.client, "_upload_s3_folder", return_value=mock_result):
            response = self.client.upload_s3_folder(
                "test-folder", "my-s3-bucket", "documents/", ProcessingMode.DEFAULT
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-s3-123"
        assert response.message == "S3 folder uploaded successfully"
        assert "file1.pdf" in response.uploads
        assert "file2.docx" in response.uploads

    def test_upload_box_folder_success(self):
        """Test successful Box folder upload"""
        mock_result = IngestionResult(
            message="Box folder uploaded successfully",
            request_id="test-req-box-456",
            uploads=["presentation.pptx", "report.docx"],
        )

        with patch.object(
            self.client, "_upload_box_folder", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_box_folder(
                "test-folder", "box-folder-123", ProcessingMode.DEFAULT
            )

            # Verify the private method was called with correct parameters
            mock_upload.assert_called_once_with(
                "box-folder-123", mode=ProcessingMode.DEFAULT, folder_id="test-folder"
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-box-456"
        assert response.message == "Box folder uploaded successfully"
        assert "presentation.pptx" in response.uploads
        assert "report.docx" in response.uploads

    def test_upload_box_folder_with_root(self):
        """Test Box folder upload with root folder (folder_id='0')"""
        mock_result = IngestionResult(
            message="Box root folder uploaded successfully",
            request_id="test-req-box-root",
            uploads=["file1.pdf"],
        )

        with patch.object(
            self.client, "_upload_box_folder", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_box_folder(
                "test-folder", "0", ProcessingMode.ADVANCED  # Root folder
            )

            mock_upload.assert_called_once_with(
                "0", mode=ProcessingMode.ADVANCED, folder_id="test-folder"
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-box-root"

    def test_upload_dropbox_folder_success(self):
        """Test successful Dropbox folder upload"""
        mock_result = IngestionResult(
            message="Dropbox folder uploaded successfully",
            request_id="test-req-dropbox-789",
            uploads=["invoice.pdf", "contract.docx"],
        )

        with patch.object(
            self.client, "_upload_dropbox_folder", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_dropbox_folder(
                "test-folder", "/Documents/Reports", ProcessingMode.DEFAULT
            )

            # Verify the private method was called with correct parameters
            mock_upload.assert_called_once_with(
                "/Documents/Reports",
                mode=ProcessingMode.DEFAULT,
                folder_id="test-folder",
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-dropbox-789"
        assert response.message == "Dropbox folder uploaded successfully"
        assert "invoice.pdf" in response.uploads
        assert "contract.docx" in response.uploads

    def test_upload_dropbox_folder_root(self):
        """Test Dropbox folder upload with root path"""
        mock_result = IngestionResult(
            message="Dropbox root uploaded successfully",
            request_id="test-req-dropbox-root",
            uploads=["root-file.txt"],
        )

        with patch.object(
            self.client, "_upload_dropbox_folder", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_dropbox_folder(
                "test-folder", "/", ProcessingMode.DEFAULT  # Root folder
            )

            mock_upload.assert_called_once_with(
                "/", mode=ProcessingMode.DEFAULT, folder_id="test-folder"
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-dropbox-root"

    def test_upload_sharepoint_folder_success(self):
        """Test successful SharePoint folder upload"""
        mock_result = IngestionResult(
            message="SharePoint folder uploaded successfully",
            request_id="test-req-sp-101",
            uploads=["policy.pdf", "guidelines.docx", "template.xlsx"],
        )

        with patch.object(
            self.client, "_upload_sharepoint_folder", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_sharepoint_folder(
                "test-folder", "drive-abc123", "folder-def456", ProcessingMode.DEFAULT
            )

            # Verify the private method was called with correct parameters
            mock_upload.assert_called_once_with(
                "drive-abc123",
                "folder-def456",
                mode=ProcessingMode.DEFAULT,
                folder_id="test-folder",
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-sp-101"
        assert response.message == "SharePoint folder uploaded successfully"
        assert "policy.pdf" in response.uploads
        assert "guidelines.docx" in response.uploads
        assert "template.xlsx" in response.uploads

    def test_upload_sharepoint_folder_root(self):
        """Test SharePoint folder upload with root folder"""
        mock_result = IngestionResult(
            message="SharePoint root uploaded successfully",
            request_id="test-req-sp-root",
            uploads=["root-document.pdf"],
        )

        with patch.object(
            self.client, "_upload_sharepoint_folder", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_sharepoint_folder(
                "test-folder",
                "drive-xyz789",
                "root",  # Root folder
                ProcessingMode.ADVANCED,
            )

            mock_upload.assert_called_once_with(
                "drive-xyz789",
                "root",
                mode=ProcessingMode.ADVANCED,
                folder_id="test-folder",
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-sp-root"

    def test_upload_salesforce_folder_success(self):
        """Test successful Salesforce folder upload"""
        mock_result = IngestionResult(
            message="Salesforce documents uploaded successfully",
            request_id="test-req-sf-202",
            uploads=["opportunity.pdf", "lead-notes.docx"],
        )

        with patch.object(
            self.client, "_upload_salesforce_folder", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_salesforce_folder(
                "test-folder", "Customer Documents", ProcessingMode.DEFAULT
            )

            # Verify the private method was called with correct parameters
            mock_upload.assert_called_once_with(
                "Customer Documents",
                mode=ProcessingMode.DEFAULT,
                folder_id="test-folder",
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-sf-202"
        assert response.message == "Salesforce documents uploaded successfully"
        assert "opportunity.pdf" in response.uploads
        assert "lead-notes.docx" in response.uploads

    def test_upload_salesforce_folder_with_custom_mode(self):
        """Test Salesforce folder upload with custom processing mode"""
        mock_result = IngestionResult(
            message="Salesforce data processed",
            request_id="test-req-sf-custom",
            uploads=["case-study.pdf"],
        )

        with patch.object(
            self.client, "_upload_salesforce_folder", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_salesforce_folder(
                "test-folder", "Case Studies", ProcessingMode.DEFAULT
            )

            mock_upload.assert_called_once_with(
                "Case Studies", mode=ProcessingMode.DEFAULT, folder_id="test-folder"
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-sf-custom"

    def test_upload_sendme_files_success(self):
        """Test successful Sendme files upload"""
        mock_result = IngestionResult(
            message="Sendme files uploaded successfully",
            request_id="test-req-sendme-303",
            uploads=["secure-doc.pdf", "confidential.docx"],
        )

        with patch.object(
            self.client, "_upload_sendme_files", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_sendme_files(
                "test-folder", "ticket-abc123xyz", ProcessingMode.DEFAULT
            )

            # Verify the private method was called with correct parameters
            mock_upload.assert_called_once_with(
                "ticket-abc123xyz", mode=ProcessingMode.DEFAULT, folder_id="test-folder"
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-sendme-303"
        assert response.message == "Sendme files uploaded successfully"
        assert "secure-doc.pdf" in response.uploads
        assert "confidential.docx" in response.uploads

    def test_upload_sendme_files_with_advanced_mode(self):
        """Test Sendme files upload with advanced processing mode"""
        mock_result = IngestionResult(
            message="Sendme files processed with advanced mode",
            request_id="test-req-sendme-advanced",
            uploads=["analysis-report.pdf"],
        )

        with patch.object(
            self.client, "_upload_sendme_files", return_value=mock_result
        ) as mock_upload:
            response = self.client.upload_sendme_files(
                "test-folder", "ticket-def456ghi", ProcessingMode.ADVANCED
            )

            mock_upload.assert_called_once_with(
                "ticket-def456ghi",
                mode=ProcessingMode.ADVANCED,
                folder_id="test-folder",
            )

        assert isinstance(response, IngestionResult)
        assert response.request_id == "test-req-sendme-advanced"


class TestHippoChatManagement:
    """Test chat management methods"""

    def setup_method(self):
        """Set up test client"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            self.client = Hippo(api_key="test-key")

    @responses.activate
    def test_create_chat_success(self):
        """Test successful chat creation"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/chats",
            json={
                "created": True,
                "status": "ok",
                "chat_id": "chat123",
                "chat_name": "Test Chat",
            },
            status=200,
        )

        response = self.client.create_chat("test-folder")

        assert isinstance(response, ChatCreatedResponse)
        assert response.created is True
        assert response.chat_id == "chat123"

    @responses.activate
    def test_get_chats_success(self):
        """Test successful chat listing"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats",
            json={
                "chats": [
                    {
                        "chat_id": "chat1",
                        "chat_name": "Chat 1",
                        "folder_id": "folder1",
                        "created": "2024-01-01T00:00:00Z",
                    }
                ]
            },
            status=200,
        )

        response = self.client.get_chats()

        assert isinstance(response, list)
        assert len(response) == 1
        assert isinstance(response[0], ChatItem)
        assert response[0].chat_id == "chat1"

    @responses.activate
    def test_get_chats_with_folder_filter(self):
        """Test chat listing with folder filter"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats",
            json={
                "chats": [
                    {
                        "chat_id": "chat1",
                        "chat_name": "Chat 1",
                        "folder_id": "test-folder",
                    }
                ]
            },
            status=200,
        )

        response = self.client.get_chats(folder_id="test-folder")

        assert len(response) == 1
        assert response[0].folder_id == "test-folder"

    @responses.activate
    def test_get_chat_by_id_success(self):
        """Test successful chat retrieval by ID"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats/chat123",
            json={
                "chat_id": "chat123",
                "chat_name": "Test Chat",
                "folder_id": "folder1",
                "created": "2024-01-01T00:00:00Z",
            },
            status=200,
        )

        response = self.client.get_chat_by_id("chat123")

        assert isinstance(response, ChatItem)
        assert response.chat_id == "chat123"
        assert response.chat_name == "Test Chat"

    @responses.activate
    def test_update_chat_success(self):
        """Test successful chat update"""
        responses.add(
            responses.PUT,
            "https://dev.cerevox.ai/v1/chats/chat123",
            json={"updated": True, "status": "ok"},
            status=200,
        )

        response = self.client.update_chat("chat123", "Updated Chat Name")

        assert isinstance(response, UpdatedResponse)
        assert response.updated is True

    @responses.activate
    def test_delete_chat_success(self):
        """Test successful chat deletion"""
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/chats/chat123",
            json={"deleted": True, "status": "ok"},
            status=200,
        )

        response = self.client.delete_chat("chat123")

        assert isinstance(response, DeletedResponse)
        assert response.deleted is True


class TestHippoAskManagement:
    """Test ask management methods (Core RAG functionality)"""

    def setup_method(self):
        """Set up test client"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            self.client = Hippo(api_key="test-key")

    @responses.activate
    def test_submit_ask_success_default(self):
        """Test successful ask submission with default parameters"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "ask_index": 1,
                "query": "What is this document about?",
                "reply": "This document is about testing.",
                "source_data": [],
            },
            status=200,
        )

        response = self.client.submit_ask("chat123", "What is this document about?")

        assert isinstance(response, AskSubmitResponse)
        assert response.query == "What is this document about?"
        assert response.reply == "This document is about testing."

    @responses.activate
    def test_submit_ask_success_with_parameters(self):
        """Test successful ask submission with all parameters"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "ask_index": 1,
                "query": "What is this document about?",
                "reply": "This document is about testing.",
                "source_data": [
                    {
                        "text": "Sample text from document",
                        "score": 0.95,
                        "metadata": {
                            "citation": "Document 1, Page 1",
                            "name": "test.pdf",
                            "type": "pdf",
                            "page": 1,
                        },
                    }
                ],
            },
            status=200,
        )

        response = self.client.submit_ask(
            "chat123",
            "What is this document about?",
            is_qna=False,
            citation_style="APA",
            sources=["file1", "file2"],
        )

        assert isinstance(response, AskSubmitResponse)
        assert response.source_data is not None
        assert len(response.source_data) == 1

    @responses.activate
    def test_get_asks_success(self):
        """Test successful ask listing"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "ask_count": 2,
                "asks": [
                    {
                        "ask_index": 1,
                        "ask_ts": 1704067200,
                        "query": "Question 1",
                        "reply": "Answer 1",
                    },
                    {
                        "ask_index": 2,
                        "ask_ts": 1704070800,
                        "query": "Question 2",
                        "reply": "Answer 2",
                    },
                ],
            },
            status=200,
        )

        response = self.client.get_asks("chat123")

        assert isinstance(response, list)
        assert len(response) == 2
        assert all(isinstance(ask, AskListItem) for ask in response)
        assert response[0].ask_index == 1

    @responses.activate
    def test_get_asks_with_custom_maxlen(self):
        """Test ask listing with custom message length"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "ask_count": 1,
                "asks": [
                    {
                        "ask_index": 1,
                        "ask_ts": 1704067200,
                        "query": "Short question",
                        "reply": "Short answer",
                    }
                ],
            },
            status=200,
        )

        response = self.client.get_asks("chat123", msg_maxlen=50)

        assert len(response) == 1
        assert response[0].query == "Short question"

    @responses.activate
    def test_get_ask_by_index_success(self):
        """Test successful ask retrieval by index"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats/chat123/asks/1",
            json={
                "ask_index": 1,
                "ask_ts": 1704067200,
                "query": "What is this document about?",
                "reply": "This document is about testing.",
            },
            status=200,
        )

        response = self.client.get_ask_by_index("chat123", 1)

        assert isinstance(response, AskItem)
        assert response.ask_index == 1

    @responses.activate
    def test_get_ask_by_index_with_options(self):
        """Test ask retrieval with show_files and show_source options"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats/chat123/asks/1",
            json={
                "ask_index": 1,
                "ask_ts": 1704067200,
                "query": "What is this document about?",
                "reply": "This document is about testing.",
                "filenames": ["test.pdf", "doc.docx"],
                "source_data": [
                    {
                        "text": "Sample text from document",
                        "score": 0.92,
                        "metadata": {
                            "citation": "Document 1",
                            "name": "test.pdf",
                            "type": "pdf",
                            "page": 1,
                        },
                    }
                ],
            },
            status=200,
        )

        response = self.client.get_ask_by_index(
            "chat123", 1, show_files=True, show_source=True
        )

        assert isinstance(response, AskItem)
        assert response.filenames is not None
        assert len(response.filenames) == 2
        assert response.source_data is not None

    @responses.activate
    def test_delete_ask_by_index_success(self):
        """Test successful ask deletion by index"""
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/chats/chat123/asks/1",
            json={"deleted": True, "status": "ok"},
            status=200,
        )

        response = self.client.delete_ask_by_index("chat123", 1)

        assert isinstance(response, DeletedResponse)
        assert response.deleted is True


class TestHippoConvenienceMethods:
    """Test convenience methods"""

    def setup_method(self):
        """Set up test client"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            self.client = Hippo(api_key="test-key")

    @responses.activate
    def test_get_folder_file_count(self):
        """Test folder file count convenience method"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            json={
                "files": [
                    {"file_id": "file1", "name": "doc1.pdf"},
                    {"file_id": "file2", "name": "doc2.pdf"},
                    {"file_id": "file3", "name": "doc3.pdf"},
                ]
            },
            status=200,
        )

        count = self.client.get_folder_file_count("test-folder")

        assert count == 3

    @responses.activate
    def test_get_chat_ask_count(self):
        """Test chat ask count convenience method"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "ask_count": 2,
                "asks": [
                    {
                        "ask_index": 1,
                        "ask_ts": 1704067200,
                        "query": "Q1",
                        "reply": "A1",
                    },
                    {
                        "ask_index": 2,
                        "ask_ts": 1704070800,
                        "query": "Q2",
                        "reply": "A2",
                    },
                ],
            },
            status=200,
        )

        count = self.client.get_chat_ask_count("chat123")

        assert count == 2


class TestHippoErrorHandling:
    """Test error handling in requests"""

    def setup_method(self):
        """Set up test client"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            self.client = Hippo(api_key="test-key")

    @responses.activate
    def test_request_timeout_error(self):
        """Test timeout error handling"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders",
            body=Timeout("Request timed out"),
        )

        with pytest.raises(LexaTimeoutError):
            self.client.get_folders()

    @responses.activate
    def test_request_connection_error(self):
        """Test connection error handling"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders",
            body=ConnectionError("Connection failed"),
        )

        with pytest.raises(LexaError):
            self.client.get_folders()

    @responses.activate
    def test_request_generic_error(self):
        """Test generic request error handling"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders",
            body=RequestException("Generic error"),
        )

        with pytest.raises(LexaError):
            self.client.get_folders()

    @responses.activate
    def test_http_error_response(self):
        """Test HTTP error response handling"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders/nonexistent",
            json={
                "error": "Folder not found",
                "message": "The requested folder does not exist",
            },
            status=404,
        )

        with pytest.raises(LexaError):
            self.client.get_folder_by_id("nonexistent")

    @responses.activate
    def test_non_json_success_response(self):
        """Test handling of non-JSON success response"""
        responses.add(
            responses.DELETE,
            "https://dev.cerevox.ai/v1/folders/test-folder",
            body="OK",
            status=200,
            content_type="text/plain",
        )

        # This should not raise an error and return a basic success response
        response_data = self.client._request("DELETE", "/folders/test-folder")
        assert response_data == {"status": "success"}

    @responses.activate
    def test_non_json_error_response(self):
        """Test handling of non-JSON error response"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders/error",
            body="Internal Server Error",
            status=500,
            content_type="text/plain",
        )

        with pytest.raises(LexaError) as exc_info:
            self.client.get_folder_by_id("error")

        # The error should contain the HTTP status and text
        assert "500" in str(exc_info.value)

    @responses.activate
    def test_error_response_json_valueerror(self):
        """Test error response handling when response.json() raises ValueError (lines 208-209)"""

        # Mock a response that will cause response.json() to raise ValueError
        def request_callback(*args, **kwargs):
            # Create a mock response that raises ValueError when .json() is called
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request - Invalid JSON"
            mock_response.headers = {"x-request-id": "test-req-123"}

            # Mock the json() method to raise ValueError
            mock_response.json.side_effect = ValueError(
                "No JSON object could be decoded"
            )

            return mock_response

        # Use the _request method directly to test the ValueError handling
        with patch.object(self.client.session, "request", side_effect=request_callback):
            with pytest.raises(LexaError) as exc_info:
                self.client._request("GET", "/test-error-endpoint")

            # Verify that the error was created with the fallback error_data structure
            # This confirms lines 208-209 were executed (ValueError exception handling)
            error = exc_info.value
            assert error.status_code == 400
            assert error.request_id == "test-req-123"
            # The error should contain "HTTP 400" which comes from the ValueError fallback
            assert "HTTP 400" in str(error)
            # Verify the response_data has the expected structure from lines 210-213
            assert error.response_data["error"] == "HTTP 400"
            assert error.response_data["message"] == "Bad Request - Invalid JSON"

    def test_close_method(self):
        """Test session close method"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            client = Hippo(api_key="test-key")

        # Should not raise any errors
        client.close()

        # Test close without session
        client_no_session = object.__new__(Hippo)
        client_no_session.close()  # Should not raise error


class TestHippoRequestHeaders:
    """Test request header handling"""

    def setup_method(self):
        """Set up test client"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://dev.cerevox.ai/v1/token/login",
                json={
                    "access_token": "test-access-token",
                    "expires_in": 3600,
                    "refresh_token": "test-refresh-token",
                    "token_type": "Bearer",
                },
                status=200,
            )
            self.client = Hippo(api_key="test-key")

    @responses.activate
    def test_request_with_custom_headers(self):
        """Test request with custom headers"""

        def request_callback(request):
            # Verify custom header is present
            assert "X-Custom-Header" in request.headers
            assert request.headers["X-Custom-Header"] == "custom-value"
            return (200, {}, json.dumps({"folders": []}))

        responses.add_callback(
            responses.GET,
            "https://dev.cerevox.ai/v1/folders",
            callback=request_callback,
        )

        # Make request with custom headers
        self.client._request(
            "GET", "/folders", headers={"X-Custom-Header": "custom-value"}
        )

    def test_file_upload_headers(self):
        """Test that upload_file calls the ingest service properly"""
        # Mock the ingest service method to test that it's called correctly
        mock_result = IngestionResult(
            message="Files uploaded successfully",
            request_id="test-req-headers",
            uploads=["test.txt"],
        )

        with patch.object(
            self.client, "_upload_files", return_value=mock_result
        ) as mock_upload:
            self.client.upload_file("test-folder", "/path/to/test.txt")

            # Verify the ingest service was called with correct parameters
            mock_upload.assert_called_once_with(
                "/path/to/test.txt",
                mode=ProcessingMode.DEFAULT,
                folder_id="test-folder",
            )
