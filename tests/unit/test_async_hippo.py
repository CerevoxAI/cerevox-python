"""
Test suite for cerevox.apis.async_hippo

Comprehensive tests to achieve 100% code coverage for the AsyncHippo class,
including all methods, error handling, and edge cases.
"""

import asyncio
import io
import os
from unittest.mock import patch

import aiohttp
import pytest
from aioresponses import aioresponses

from cerevox import AsyncHippo
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
    LexaAuthError,
    LexaError,
    LexaTimeoutError,
    MessageResponse,
    TokenResponse,
    UpdatedResponse,
)


@pytest.fixture
def mock_login_response():
    """Standard login response for mocking"""
    return {
        "access_token": "test-access-token",
        "expires_in": 3600,
        "refresh_token": "test-refresh-token",
        "token_type": "Bearer",
    }


def setup_login_mock(mock, login_response=None):
    """Helper to setup login mock"""
    if login_response is None:
        login_response = {
            "access_token": "test-access-token",
            "expires_in": 3600,
            "refresh_token": "test-refresh-token",
            "token_type": "Bearer",
        }

    mock.post(
        "https://dev.cerevox.ai/v1/token/login",
        payload=login_response,
        status=200,
    )


class TestAsyncHippoInitialization:
    """Test AsyncHippo client initialization"""

    def setup_method(self):
        """Set up test fixtures with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during client initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    def test_init_with_api_key(self):
        """Test initialization with API key parameter"""
        client = AsyncHippo(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.data_url == "https://data.cerevox.ai"
        assert client.timeout.total == 30.0
        assert client.max_retries == 3
        assert (
            "Authorization" not in client.session_kwargs["headers"]
        )  # Not set until login

    def test_init_missing_credentials(self):
        """Test initialization fails without credentials"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="api_key is required for authentication"
            ):
                AsyncHippo(api_key=None)

    def test_init_invalid_data_url(self):
        """Test initialization with invalid base URL"""
        with pytest.raises(ValueError, match="data_url must start with"):
            AsyncHippo(api_key="test-key", data_url="invalid-url")

    def test_init_invalid_max_retries(self):
        """Test initialization with invalid max_retries"""
        with pytest.raises(TypeError, match="max_retries must be an integer"):
            AsyncHippo(api_key="test-key", max_retries="invalid")

        with pytest.raises(
            ValueError, match="max_retries must be a non-negative integer"
        ):
            AsyncHippo(api_key="test-key", max_retries=-1)

    def test_init_custom_parameters(self):
        """Test initialization with custom parameters"""
        custom_timeout = aiohttp.ClientTimeout(total=60.0)
        client = AsyncHippo(
            email="test@example.com",
            api_key="test-key",
            data_url="http://localhost:8000/v1",
            timeout=60.0,
            max_retries=5,
            custom_param="test",
        )

        assert client.data_url == "http://localhost:8000/v1"
        assert client.timeout.total == 60.0
        assert client.max_retries == 5
        assert "custom_param" in client.session_kwargs

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with AsyncHippo(api_key="test-key") as client:
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)

        # Session should be closed after context exit
        assert client.session is None or client.session.closed

    @pytest.mark.asyncio
    async def test_start_and_close_session(self):
        """Test manual session management"""
        client = AsyncHippo(api_key="test-key")

        # Session should be None initially
        assert client.session is None

        await client.start_session()
        assert client.session is not None

        await client.close_session()
        assert client.session is None


class TestAsyncHippoAuthentication:
    """Test authentication methods"""

    def setup_method(self):
        """Set up test client with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/login",
            payload={
                "access_token": "test-access-token",
                "expires_in": 3600,
                "refresh_token": "test-refresh-token",
                "token_type": "Bearer",
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client._login("test-api-key")

            assert isinstance(response, TokenResponse)
            assert response.access_token == "test-access-token"
            assert (
                "Bearer test-access-token"
                in client.session_kwargs["headers"]["Authorization"]
            )

    @pytest.mark.asyncio
    async def test_login_failure(self):
        """Test login failure"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/login",
            payload={"error": "Invalid credentials"},
            status=401,
        )

        async with AsyncHippo(api_key="test-key") as client:
            with pytest.raises(LexaAuthError):
                await client._login("wrong-api-key")

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh"""
        # Token refresh
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/refresh",
            payload={
                "access_token": "refreshed-access-token",
                "expires_in": 3600,
                "refresh_token": "new-refresh-token",
                "token_type": "Bearer",
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client._refresh_token("old-refresh-token")

            assert isinstance(response, TokenResponse)
            assert response.access_token == "refreshed-access-token"
            assert (
                "Bearer refreshed-access-token"
                in client.session_kwargs["headers"]["Authorization"]
            )

    @pytest.mark.asyncio
    async def test_revoke_token_success(self):
        """Test successful token revocation"""
        # Token revocation
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/revoke",
            payload={"message": "Token revoked successfully", "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client._revoke_token()

            assert isinstance(response, MessageResponse)
            assert response.message == "Token revoked successfully"

    @pytest.mark.asyncio
    async def test_revoke_token_fail(self):
        """Test failed token revocation"""
        # Token revocation
        self.mock.post(
            "https://dev.cerevox.ai/v1/token/revoke",
            payload={"message": "Token revoked successfully", "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            del client.session_kwargs["headers"]["Authorization"]
            response = await client._revoke_token()

            assert isinstance(response, MessageResponse)
            assert response.message == "Token revoked successfully"

    @pytest.mark.asyncio
    async def test_refresh_token_with_none_session(self):
        """Test refresh_token when self.session is None (for code coverage)"""
        client = AsyncHippo(api_key="test-key")
        await client.start_session()

        try:
            # Mock the _request method to simulate successful API response
            mock_response_data = {
                "access_token": "refreshed-access-token",
                "expires_in": 3600,
                "refresh_token": "new-refresh-token",
                "token_type": "Bearer",
            }

            with patch.object(client, "_request", return_value=mock_response_data):
                # Store original session
                original_session = client.session

                # Set session to None after the API call but before header update
                # This will trigger the condition at line 280 to be False
                client.session = None

                response = await client._refresh_token("old-refresh-token")

                # Should still return a valid TokenResponse
                assert isinstance(response, TokenResponse)
                assert response.access_token == "refreshed-access-token"
                # The if self.session: block should be skipped, so no headers are updated

                # Restore session for cleanup
                client.session = original_session
        finally:
            await client.close_session()

    @pytest.mark.asyncio
    async def test_login_with_none_session(self):
        """Test login when self.session is None (for code coverage)"""
        client = AsyncHippo(api_key="test-key")
        await client.start_session()

        try:
            # Mock the _request method to simulate successful API response
            mock_response_data = {
                "access_token": "refreshed-access-token",
                "expires_in": 3600,
                "refresh_token": "new-refresh-token",
                "token_type": "Bearer",
            }

            with patch.object(client, "_request", return_value=mock_response_data):
                # Store original session
                original_session = client.session

                # Set session to None after the API call but before header update
                # This will trigger the condition at line 280 to be False
                client.session = None

                response = await client._login("test-api-key")

                # Should still return a valid TokenResponse
                assert isinstance(response, TokenResponse)
                assert response.access_token == "refreshed-access-token"
                # The if self.session: block should be skipped, so no headers are updated

                # Restore session for cleanup
                client.session = original_session
        finally:
            await client.close_session()


class TestAsyncHippoFolderManagement:
    """Test folder management methods"""

    def setup_method(self):
        """Set up test client with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_create_folder_success(self):
        """Test successful folder creation"""
        # Create folder
        self.mock.post(
            "https://dev.cerevox.ai/v1/folders",
            payload={
                "created": True,
                "status": "ok",
                "folder_id": "test-folder",
                "folder_name": "Test Folder",
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.create_folder("test-folder", "Test Folder")

            assert isinstance(response, FolderCreatedResponse)
            assert response.created is True
            assert response.folder_id == "test-folder"
            assert response.folder_name == "Test Folder"

    @pytest.mark.asyncio
    async def test_get_folders_success(self):
        """Test successful folder listing"""
        # Get folders
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders",
            payload={
                "folders": [
                    {"folder_id": "folder1", "folder_name": "Folder 1"},
                    {"folder_id": "folder2", "folder_name": "Folder 2"},
                ]
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_folders()

            assert isinstance(response, list)
            assert len(response) == 2
            assert all(isinstance(folder, FolderItem) for folder in response)
            assert response[0].folder_id == "folder1"

    @pytest.mark.asyncio
    async def test_get_folders_with_search(self):
        """Test folder listing with search parameter"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders?search_name=test",
            payload={
                "folders": [{"folder_id": "folder1", "folder_name": "Test Folder"}]
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_folders(search_name="test")

            assert len(response) == 1
            assert response[0].folder_name == "Test Folder"

    @pytest.mark.asyncio
    async def test_get_folder_by_id_success(self):
        """Test successful folder retrieval by ID"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders/test-folder",
            payload={
                "folder_id": "test-folder",
                "folder_name": "Test Folder",
                "status": "ready",
                "currentSize": 1024,
                "historicalSize": 2048,
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_folder_by_id("test-folder")

            assert isinstance(response, FolderItem)
            assert response.folder_id == "test-folder"
            assert response.status == "ready"
            assert response.currentSize == 1024

    @pytest.mark.asyncio
    async def test_update_folder_success(self):
        """Test successful folder update"""
        self.mock.put(
            "https://dev.cerevox.ai/v1/folders/test-folder",
            payload={"updated": True, "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.update_folder("test-folder", "Updated Folder Name")

            assert isinstance(response, UpdatedResponse)
            assert response.updated is True

    @pytest.mark.asyncio
    async def test_delete_folder_success(self):
        """Test successful folder deletion"""
        self.mock.delete(
            "https://dev.cerevox.ai/v1/folders/test-folder",
            payload={"deleted": True, "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.delete_folder("test-folder")

            assert isinstance(response, DeletedResponse)
            assert response.deleted is True


class TestAsyncHippoFileManagement:
    """Test file management methods"""

    def setup_method(self):
        """Set up test client with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_upload_file_success(self):
        """Test successful file upload"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            payload={"uploaded": True, "status": "ok", "uploads": ["test.txt"]},
        )

        async with AsyncHippo(api_key="test-key") as client:
            # Create a real BytesIO object instead of mock_open
            fake_file = io.BytesIO(b"test content")
            with patch("builtins.open", return_value=fake_file):
                with patch("os.path.basename", return_value="test.txt"):
                    response = await client.upload_file(
                        "test-folder", "/path/to/test.txt"
                    )

            assert isinstance(response, FileUploadResponse)
            assert response.uploaded is True
            assert "test.txt" in response.uploads

    @pytest.mark.asyncio
    async def test_upload_file_from_url_success(self):
        """Test successful file upload from URL"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/folders/test-folder/files/url",
            payload={
                "uploaded": True,
                "status": "ok",
                "uploads": ["remote-file.pdf"],
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            files = [
                {
                    "url": "https://example.com/file.pdf",
                    "filename": "remote-file.pdf",
                }
            ]
            response = await client.upload_file_from_url("test-folder", files)

            assert isinstance(response, FileUploadResponse)
            assert response.uploaded is True

    @pytest.mark.asyncio
    async def test_get_files_success(self):
        """Test successful file listing"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            payload={
                "files": [
                    {
                        "file_id": "file1",
                        "name": "document1.pdf",
                        "size": 1024,
                        "type": "application/pdf",
                    }
                ]
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_files("test-folder")

            assert isinstance(response, list)
            assert len(response) == 1
            assert isinstance(response[0], FileItem)
            assert response[0].file_id == "file1"

    @pytest.mark.asyncio
    async def test_get_files_with_search(self):
        """Test file listing with search parameter"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders/test-folder/files?search_name=test",
            payload={
                "files": [
                    {
                        "file_id": "file1",
                        "name": "test-document.pdf",
                        "size": 1024,
                        "type": "application/pdf",
                    }
                ]
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_files("test-folder", search_name="test")

            assert len(response) == 1
            assert response[0].name == "test-document.pdf"

    @pytest.mark.asyncio
    async def test_get_file_by_id_success(self):
        """Test successful file retrieval by ID"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders/test-folder/files/file1",
            payload={
                "file_id": "file1",
                "name": "document.pdf",
                "size": 2048,
                "type": "application/pdf",
                "provider": "local",
                "source": "upload",
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_file_by_id("test-folder", "file1")

            assert isinstance(response, FileItem)
            assert response.file_id == "file1"
            assert response.size == 2048

    @pytest.mark.asyncio
    async def test_delete_file_by_id_success(self):
        """Test successful file deletion by ID"""
        self.mock.delete(
            "https://dev.cerevox.ai/v1/folders/test-folder/files/file1",
            payload={"deleted": True, "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.delete_file_by_id("test-folder", "file1")

            assert isinstance(response, DeletedResponse)
            assert response.deleted is True

    @pytest.mark.asyncio
    async def test_delete_all_files_success(self):
        """Test successful deletion of all files"""
        self.mock.delete(
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            payload={"deleted": True, "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.delete_all_files("test-folder")

            assert isinstance(response, DeletedResponse)
            assert response.deleted is True


class TestAsyncHippoChatManagement:
    """Test chat management methods"""

    def setup_method(self):
        """Set up test client with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_create_chat_success(self):
        """Test successful chat creation"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/chats",
            payload={
                "created": True,
                "status": "ok",
                "chat_id": "chat123",
                "chat_name": "Test Chat",
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.create_chat("test-folder")

            assert isinstance(response, ChatCreatedResponse)
            assert response.created is True
            assert response.chat_id == "chat123"

    @pytest.mark.asyncio
    async def test_get_chats_success(self):
        """Test successful chat listing"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/chats",
            payload={
                "chats": [
                    {
                        "chat_id": "chat1",
                        "chat_name": "Chat 1",
                        "folder_id": "folder1",
                        "created": "2024-01-01T00:00:00Z",
                    }
                ]
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_chats()

            assert isinstance(response, list)
            assert len(response) == 1
            assert isinstance(response[0], ChatItem)
            assert response[0].chat_id == "chat1"

    @pytest.mark.asyncio
    async def test_get_chats_with_folder_filter(self):
        """Test chat listing with folder filter"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/chats?folder_id=test-folder",
            payload={
                "chats": [
                    {
                        "chat_id": "chat1",
                        "chat_name": "Chat 1",
                        "folder_id": "test-folder",
                    }
                ]
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_chats(folder_id="test-folder")

            assert len(response) == 1
            assert response[0].folder_id == "test-folder"

    @pytest.mark.asyncio
    async def test_get_chat_by_id_success(self):
        """Test successful chat retrieval by ID"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/chats/chat123",
            payload={
                "chat_id": "chat123",
                "chat_name": "Test Chat",
                "folder_id": "folder1",
                "created": "2024-01-01T00:00:00Z",
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_chat_by_id("chat123")

            assert isinstance(response, ChatItem)
            assert response.chat_id == "chat123"
            assert response.chat_name == "Test Chat"

    @pytest.mark.asyncio
    async def test_update_chat_success(self):
        """Test successful chat update"""
        self.mock.put(
            "https://dev.cerevox.ai/v1/chats/chat123",
            payload={"updated": True, "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.update_chat("chat123", "Updated Chat Name")

            assert isinstance(response, UpdatedResponse)
            assert response.updated is True

    @pytest.mark.asyncio
    async def test_delete_chat_success(self):
        """Test successful chat deletion"""
        self.mock.delete(
            "https://dev.cerevox.ai/v1/chats/chat123",
            payload={"deleted": True, "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.delete_chat("chat123")

            assert isinstance(response, DeletedResponse)
            assert response.deleted is True


class TestAsyncHippoAskManagement:
    """Test ask management methods (Core RAG functionality)"""

    def setup_method(self):
        """Set up test client with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_submit_ask_success_default(self):
        """Test successful ask submission with default parameters"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            payload={
                "ask_index": 1,
                "query": "What is this document about?",
                "reply": "This document is about testing.",
                "source_data": [],
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.submit_ask(
                "chat123", "What is this document about?"
            )

            assert isinstance(response, AskSubmitResponse)
            assert response.query == "What is this document about?"
            assert response.reply == "This document is about testing."

    @pytest.mark.asyncio
    async def test_submit_ask_success_with_parameters(self):
        """Test successful ask submission with all parameters"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/chats/chat123/asks",
            payload={
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
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.submit_ask(
                "chat123",
                "What is this document about?",
                citation_style="APA",
                source_ids=["file1", "file2"],
            )

            assert isinstance(response, AskSubmitResponse)
            assert response.source_data is not None
            assert len(response.source_data) == 1

    @pytest.mark.asyncio
    async def test_get_asks_success(self):
        """Test successful ask listing"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/chats/chat123/asks?msg_maxlen=120",
            payload={
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
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_asks("chat123")

            assert isinstance(response, list)
            assert len(response) == 2
            assert all(isinstance(ask, AskListItem) for ask in response)
            assert response[0].ask_index == 1

    @pytest.mark.asyncio
    async def test_get_asks_with_custom_maxlen(self):
        """Test ask listing with custom message length"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/chats/chat123/asks?msg_maxlen=50",
            payload={
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
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_asks("chat123", msg_maxlen=50)

            assert len(response) == 1
            assert response[0].query == "Short question"

    @pytest.mark.asyncio
    async def test_get_ask_by_index_success(self):
        """Test successful ask retrieval by index"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/chats/chat123/asks/1",
            payload={
                "ask_index": 1,
                "ask_ts": 1704067200,
                "query": "What is this document about?",
                "reply": "This document is about testing.",
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_ask_by_index("chat123", 1)

            assert isinstance(response, AskItem)
            assert response.ask_index == 1

    @pytest.mark.asyncio
    async def test_get_ask_by_index_with_options(self):
        """Test ask retrieval with show_files and show_source options"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/chats/chat123/asks/1?show_files=true&show_source=true",
            payload={
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
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.get_ask_by_index(
                "chat123", 1, show_files=True, show_source=True
            )

            assert isinstance(response, AskItem)
            assert response.filenames is not None
            assert len(response.filenames) == 2
            assert response.source_data is not None

    @pytest.mark.asyncio
    async def test_delete_ask_by_index_success(self):
        """Test successful ask deletion by index"""
        self.mock.delete(
            "https://dev.cerevox.ai/v1/chats/chat123/asks/1",
            payload={"deleted": True, "status": "ok"},
        )

        async with AsyncHippo(api_key="test-key") as client:
            response = await client.delete_ask_by_index("chat123", 1)

            assert isinstance(response, DeletedResponse)
            assert response.deleted is True


class TestAsyncHippoConvenienceMethods:
    """Test convenience methods"""

    def setup_method(self):
        """Set up test client with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_get_folder_file_count(self):
        """Test folder file count convenience method"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            payload={
                "files": [
                    {"file_id": "file1", "name": "doc1.pdf"},
                    {"file_id": "file2", "name": "doc2.pdf"},
                    {"file_id": "file3", "name": "doc3.pdf"},
                ]
            },
        )

        async with AsyncHippo(api_key="test-key") as client:
            count = await client.get_folder_file_count("test-folder")

            assert count == 3

    @pytest.mark.asyncio
    async def test_get_chat_ask_count(self):
        """Test chat ask count convenience method"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/chats/chat123/asks?msg_maxlen=120",
            payload={
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
        )

        async with AsyncHippo(api_key="test-key") as client:
            count = await client.get_chat_ask_count("chat123")

            assert count == 2


class TestAsyncHippoErrorHandling:
    """Test error handling in requests"""

    def setup_method(self):
        """Set up test client with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_request_timeout_error(self):
        """Test timeout error handling"""
        async with AsyncHippo(api_key="test-key") as client:
            # Mock timeout
            with patch.object(client.session, "request") as mock_request:
                mock_request.side_effect = asyncio.TimeoutError("Request timed out")

                with pytest.raises(LexaTimeoutError):
                    await client.get_folders()

    @pytest.mark.asyncio
    async def test_request_connection_error(self):
        """Test connection error handling"""
        async with AsyncHippo(api_key="test-key") as client:
            # Mock connection error
            with patch.object(client.session, "request") as mock_request:
                mock_request.side_effect = aiohttp.ClientError("Connection failed")

                with pytest.raises(LexaError):
                    await client.get_folders()

    @pytest.mark.asyncio
    async def test_http_error_response(self):
        """Test HTTP error response handling"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders/nonexistent",
            payload={
                "error": "Folder not found",
                "message": "The requested folder does not exist",
            },
            status=404,
        )

        async with AsyncHippo(api_key="test-key") as client:
            with pytest.raises(LexaError):
                await client.get_folder_by_id("nonexistent")

    @pytest.mark.asyncio
    async def test_non_json_success_response(self):
        """Test handling of non-JSON success response"""
        self.mock.delete(
            "https://dev.cerevox.ai/v1/folders/test-folder",
            body="OK",
            status=200,
            content_type="text/plain",
        )

        async with AsyncHippo(api_key="test-key") as client:
            # This should not raise an error and return a basic success response
            response_data = await client._request("DELETE", "/folders/test-folder")
            assert response_data == {"status": "success"}

    @pytest.mark.asyncio
    async def test_non_json_error_response(self):
        """Test handling of non-JSON error response"""
        self.mock.get(
            "https://dev.cerevox.ai/v1/folders/error",
            body="Internal Server Error",
            status=500,
            content_type="text/plain",
        )

        async with AsyncHippo(api_key="test-key") as client:
            with pytest.raises(LexaError) as exc_info:
                await client.get_folder_by_id("error")

            # The error should contain the HTTP status
            assert "500" in str(exc_info.value) or "Internal Server Error" in str(
                exc_info.value
            )


class TestAsyncHippoRequestHeaders:
    """Test request header handling"""

    def setup_method(self):
        """Set up test client with mocked login"""
        self.mock_patcher = aioresponses()
        self.mock = self.mock_patcher.__enter__()
        # Mock the login call that happens during initialization
        setup_login_mock(self.mock)

    def teardown_method(self):
        """Clean up mocks"""
        self.mock_patcher.__exit__(None, None, None)

    @pytest.mark.asyncio
    async def test_request_with_custom_headers(self):
        """Test request with custom headers"""
        self.mock.get("https://dev.cerevox.ai/v1/folders", payload={"folders": []})

        async with AsyncHippo(api_key="test-key") as client:
            # Make request with custom headers - just verify it doesn't error
            response = await client._request(
                "GET", "/folders", headers={"X-Custom-Header": "custom-value"}
            )
            assert response == {"folders": []}

    @pytest.mark.asyncio
    async def test_file_upload_headers(self):
        """Test that file upload works correctly"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            payload={"uploaded": True, "status": "ok", "uploads": ["test.txt"]},
        )

        async with AsyncHippo(api_key="test-key") as client:
            # Create a real BytesIO object instead of mock_open
            fake_file = io.BytesIO(b"test content")
            with patch("builtins.open", return_value=fake_file):
                with patch("os.path.basename", return_value="test.txt"):
                    response = await client.upload_file(
                        "test-folder", "/path/to/test.txt"
                    )
                    assert response.uploaded is True

    @pytest.mark.asyncio
    async def test_json_vs_form_data_request(self):
        """Test that requests handle JSON vs FormData correctly"""
        self.mock.post(
            "https://dev.cerevox.ai/v1/folders",
            payload={
                "created": True,
                "status": "ok",
                "folder_id": "test",
                "folder_name": "Test",
            },
        )
        self.mock.post(
            "https://dev.cerevox.ai/v1/folders/test-folder/files",
            payload={"uploaded": True, "status": "ok", "uploads": ["test.txt"]},
        )

        async with AsyncHippo(api_key="test-key") as client:
            # Test JSON request
            response1 = await client.create_folder("test", "Test")
            assert response1.created is True

            # Test FormData request
            fake_file = io.BytesIO(b"test content")
            with patch("builtins.open", return_value=fake_file):
                with patch("os.path.basename", return_value="test.txt"):
                    response2 = await client.upload_file(
                        "test-folder", "/path/to/test.txt"
                    )
                    assert response2.uploaded is True
