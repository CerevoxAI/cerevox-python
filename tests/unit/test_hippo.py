"""
Test suite for cerevox.hippo

Comprehensive tests to achieve 100% code coverage for the Hippo class,
including all methods, error handling, and edge cases.
"""

import base64
import json
import os
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import responses
from requests.exceptions import ConnectionError, RequestException, Timeout

from cerevox.exceptions import (
    LexaAuthError,
    LexaError,
    LexaTimeoutError,
    create_error_from_response,
)
from cerevox.hippo import Hippo
from cerevox.models import (
    AskItem,
    AsksListResponse,
    AskSubmitRequest,
    ChatCreate,
    ChatCreatedResponse,
    ChatItem,
    ChatsListResponse,
    DeletedResponse,
    FileItem,
    FilesListResponse,
    FileUploadResponse,
    FolderCreate,
    FolderCreatedResponse,
    FolderItem,
    FoldersListResponse,
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
    UpdatedResponse,
)


class TestHippoInitialization:
    """Test Hippo client initialization"""

    def test_init_with_email_and_api_key(self):
        """Test initialization with email and API key parameters"""
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

            client = Hippo(email="test@example.com", api_key="test-api-key")
            assert client.email == "test@example.com"
            assert client.api_key == "test-api-key"
            assert client.base_url == "https://dev.cerevox.ai/v1"
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

                client = Hippo(email="test@example.com", api_key=None)
                assert client.api_key == "env-api-key"

    def test_init_missing_credentials(self):
        """Test initialization fails without credentials"""
        with pytest.raises(ValueError, match="Both email and api_key are required"):
            Hippo(email="", api_key="")

    def test_init_invalid_base_url(self):
        """Test initialization with invalid base URL"""
        with pytest.raises(ValueError, match="base_url must be a non-empty string"):
            Hippo(email="test@example.com", api_key="test-key", base_url="")

        with pytest.raises(ValueError, match="base_url must start with"):
            Hippo(email="test@example.com", api_key="test-key", base_url="invalid-url")

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters"""
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "http://localhost:8000/v1/token/login",
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
                base_url="http://localhost:8000/v1",
                timeout=60.0,
                max_retries=5,
                session_kwargs=session_kwargs,
                custom_param="test",
            )

            assert client.base_url == "http://localhost:8000/v1"
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

            with Hippo(email="test@example.com", api_key="test-key") as client:
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
            self.client = Hippo(email="test@example.com", api_key="test-key")

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

        response = self.client.login("test@example.com", "password")

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
            self.client.login("test@example.com", "wrong-password")

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

        response = self.client.refresh_token("old-refresh-token")

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

        response = self.client.revoke_token()

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
            self.client = Hippo(email="test@example.com", api_key="test-key")

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
            self.client = Hippo(email="test@example.com", api_key="test-key")

    @responses.activate
    def test_upload_file_success(self):
        """Test successful file upload"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            json={"uploaded": True, "status": "ok", "uploads": ["test.txt"]},
            status=200,
        )

        with patch("builtins.open", mock_open(read_data=b"test content")):
            with patch("os.path.basename", return_value="test.txt"):
                response = self.client.upload_file("test-folder", "/path/to/test.txt")

        assert isinstance(response, FileUploadResponse)
        assert response.uploaded is True
        assert "test.txt" in response.uploads

    @responses.activate
    def test_upload_file_from_url_success(self):
        """Test successful file upload from URL"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/folders/test-folder/files/url",
            json={"uploaded": True, "status": "ok", "uploads": ["remote-file.pdf"]},
            status=200,
        )

        files = [{"url": "https://example.com/file.pdf", "filename": "remote-file.pdf"}]
        response = self.client.upload_file_from_url("test-folder", files)

        assert isinstance(response, FileUploadResponse)
        assert response.uploaded is True

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
            self.client = Hippo(email="test@example.com", api_key="test-key")

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

        response = self.client.create_chat("test-folder", "openai-key")

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
            self.client = Hippo(email="test@example.com", api_key="test-key")

    @responses.activate
    def test_submit_ask_success_default(self):
        """Test successful ask submission with default parameters"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "ask_index": 1,
                "datetime": "2024-01-01T00:00:00Z",
                "query": "What is this document about?",
                "response": "This document is about testing.",
            },
            status=200,
        )

        response = self.client.submit_ask("chat123", "What is this document about?")

        assert isinstance(response, AskItem)
        assert response.query == "What is this document about?"
        assert response.response == "This document is about testing."

    @responses.activate
    def test_submit_ask_success_with_parameters(self):
        """Test successful ask submission with all parameters"""
        responses.add(
            responses.POST,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "ask_index": 1,
                "datetime": "2024-01-01T00:00:00Z",
                "query": "What is this document about?",
                "response": "This document is about testing.",
                "source_data": [
                    {
                        "citation": "Document 1, Page 1",
                        "name": "test.pdf",
                        "type": "pdf",
                        "page": 1,
                        "text_blocks": ["Sample text"],
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
            file_sources=["file1", "file2"],
        )

        assert isinstance(response, AskItem)
        assert response.source_data is not None
        assert len(response.source_data) == 1

    @responses.activate
    def test_get_asks_success(self):
        """Test successful ask listing"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "asks": [
                    {
                        "ask_index": 1,
                        "datetime": "2024-01-01T00:00:00Z",
                        "query": "Question 1",
                        "response": "Answer 1",
                    },
                    {
                        "ask_index": 2,
                        "datetime": "2024-01-01T01:00:00Z",
                        "query": "Question 2",
                        "response": "Answer 2",
                    },
                ]
            },
            status=200,
        )

        response = self.client.get_asks("chat123")

        assert isinstance(response, list)
        assert len(response) == 2
        assert all(isinstance(ask, AskItem) for ask in response)
        assert response[0].ask_index == 1

    @responses.activate
    def test_get_asks_with_custom_maxlen(self):
        """Test ask listing with custom message length"""
        responses.add(
            responses.GET,
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            json={
                "asks": [
                    {
                        "ask_index": 1,
                        "datetime": "2024-01-01T00:00:00Z",
                        "query": "Short question",
                        "response": "Short answer",
                    }
                ]
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
                "datetime": "2024-01-01T00:00:00Z",
                "query": "What is this document about?",
                "response": "This document is about testing.",
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
                "datetime": "2024-01-01T00:00:00Z",
                "query": "What is this document about?",
                "response": "This document is about testing.",
                "filenames": ["test.pdf", "doc.docx"],
                "source_data": [
                    {
                        "citation": "Document 1",
                        "name": "test.pdf",
                        "type": "pdf",
                        "page": 1,
                        "text_blocks": ["Sample text"],
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
            self.client = Hippo(email="test@example.com", api_key="test-key")

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
                "asks": [
                    {"ask_index": 1, "query": "Q1", "response": "A1"},
                    {"ask_index": 2, "query": "Q2", "response": "A2"},
                ]
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
            self.client = Hippo(email="test@example.com", api_key="test-key")

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
            client = Hippo(email="test@example.com", api_key="test-key")

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
            self.client = Hippo(email="test@example.com", api_key="test-key")

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

    @responses.activate
    def test_file_upload_headers(self):
        """Test that Content-Type header is removed for file uploads"""

        def request_callback(request):
            # Content-Type should not be manually set for file uploads
            # It should be set by requests library with boundary
            content_type = request.headers.get("Content-Type", "")
            assert "multipart/form-data" in content_type or content_type == ""
            return (
                200,
                {},
                json.dumps({"uploaded": True, "status": "ok", "uploads": ["test.txt"]}),
            )

        responses.add_callback(
            responses.POST,
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            callback=request_callback,
        )

        with patch("builtins.open", mock_open(read_data=b"test content")):
            with patch("os.path.basename", return_value="test.txt"):
                self.client.upload_file("test-folder", "/path/to/test.txt")
