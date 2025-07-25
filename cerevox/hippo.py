"""
Cerevox SDK's Synchronous Hippo Client for RAG Operations
"""

import base64
import logging
import os
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    LexaAuthError,
    LexaError,
    LexaTimeoutError,
    create_error_from_response,
)
from .models import (
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

HTTP = "http://"
HTTPS = "https://"
FAILED_ID = "Failed to get request ID from response"

logger = logging.getLogger(__name__)


class Hippo:
    """
    Official Synchronous Python Client for Cerevox Hippo (RAG Operations)

    This client provides a clean, Pythonic interface to the Cerevox RAG API,
    supporting folder management, file uploads, chat creation, and AI-powered
    question answering on your documents.

    Example:
        >>> client = Hippo(email="user@example.com", api_key="password")
        >>> # Client automatically authenticates during initialization
        >>> # Create folder and upload files
        >>> client.create_folder("docs", "My Documents")
        >>> client.upload_file("docs", "/path/to/document.pdf")
        >>> # Create chat and ask questions
        >>> chat = client.create_chat("docs", "your-openai-key")
        >>> response = client.submit_ask(chat["chat_id"], "What is this document about?")
        >>> print(response["response"])

    Happy RAG Processing! 🔍 ✨
    """

    def __init__(
        self,
        *,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://dev.cerevox.ai/v1",
        max_retries: int = 3,
        session_kwargs: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Hippo client and automatically authenticate

        Args:
            email: User email address for authentication
            api_key: User password for authentication
            base_url: Base URL for the Cerevox RAG API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            session_kwargs: Additional arguments to pass to requests.Session
        """
        self.email = email
        self.api_key = api_key or os.getenv("CEREVOX_API_KEY")
        if not self.email or not self.api_key:
            raise ValueError("Both email and api_key are required for authentication")

        # Validate base_url format
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string")

        # Basic URL validation
        if not (base_url.startswith(HTTP) or base_url.startswith(HTTPS)):
            raise ValueError(f"base_url must start with {HTTP} or {HTTPS}")

        self.base_url = base_url.rstrip("/")  # Remove trailing slash
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize session
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[500, 501, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=0.1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount(HTTP, adapter)
        self.session.mount(HTTPS, adapter)

        # Set default headers
        self.session.headers.update(
            {
                "User-Agent": "cerevox-python/0.1.6",
            }
        )

        # Apply session configuration
        if session_kwargs:
            for key, value in session_kwargs.items():
                setattr(self.session, key, value)

        # Apply any additional session configuration for backward compatibility
        for key, value in kwargs.items():
            setattr(self.session, key, value)

        # Automatically authenticate using email and password
        self.login(self.email, self.api_key)

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        All requests to Hippo API are handled by this method

        Args:
            method: The HTTP method to use
            endpoint: The API endpoint to call
            json_data: JSON data to send in the request body
            params: Query parameters to send in the request
            headers: Additional headers to send with the request
            files: Files to upload (for multipart requests)
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the API

        Raises:
            LexaAuthError: If authentication fails
            LexaError: If the request fails for other reasons
            LexaTimeoutError: If the request times out
            Various other LexaError subclasses: Based on response status and content
        """
        url = f"{self.base_url}{endpoint}"

        # Merge additional headers
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=request_headers,
                files=files,
                timeout=self.timeout,
                **kwargs,
            )

            # Extract request ID for error reporting
            request_id = response.headers.get("x-request-id", FAILED_ID)

            # Handle successful responses
            if 200 <= response.status_code < 300:
                try:
                    response_data: Dict[str, Any] = response.json()
                    return response_data
                except ValueError:
                    # Non-JSON response, return basic success info
                    return {"status": "success"}

            # Handle error responses
            try:
                error_data = response.json()
            except ValueError:
                error_data = {
                    "error": f"HTTP {response.status_code}",
                    "message": response.text,
                }

            # Create and raise appropriate exception
            raise create_error_from_response(
                status_code=response.status_code,
                response_data=error_data,
                request_id=request_id,
            )

        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout for {method} {url}: {e}")
            raise LexaTimeoutError(
                "Request timed out", timeout_duration=self.timeout
            ) from e

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {method} {url}: {e}")
            raise LexaError(f"Request failed: {e}", request_id=FAILED_ID) from e

    # Authentication Methods

    def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate with email and password to get access tokens

        Args:
            email: User email address
            password: User password

        Returns:
            TokenResponse containing access_token, refresh_token, etc.

        Raises:
            LexaAuthError: If authentication fails
        """
        # Use Basic Auth for login
        credentials = f"{email}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {"Authorization": f"Basic {encoded_credentials}"}

        response_data = self._request("POST", "/token/login", headers=headers)

        token_response = TokenResponse(**response_data)

        self.session.headers.update(
            {"Authorization": f"Bearer {token_response.access_token}"}
        )

        return token_response

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: The refresh token

        Returns:
            TokenResponse with new tokens
        """
        request = TokenRefreshRequest(refresh_token=refresh_token)
        response_data = self._request(
            "POST", "/token/refresh", json_data=request.model_dump()
        )
        token_response = TokenResponse(**response_data)

        self.session.headers.update(
            {"Authorization": f"Bearer {token_response.access_token}"}
        )

        return token_response

    def revoke_token(self) -> MessageResponse:
        """
        Revoke the current access token

        Returns:
            MessageResponse with revocation confirmation
        """
        response_data = self._request("POST", "/token/revoke")
        return MessageResponse(**response_data)

    def close(self) -> None:
        """Close the HTTP session"""
        if hasattr(self, "session"):
            self.session.close()

    def __enter__(self) -> "Hippo":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit"""
        self.close()

    # Folder Management Methods

    def create_folder(self, folder_id: str, folder_name: str) -> FolderCreatedResponse:
        """
        Create a new folder for document organization

        Args:
            folder_id: Unique identifier for the folder
            folder_name: Display name for the folder

        Returns:
            FolderCreatedResponse containing creation confirmation
        """
        request = FolderCreate(folder_id=folder_id, folder_name=folder_name)
        response_data = self._request(
            "POST", "/folders", json_data=request.model_dump()
        )
        return FolderCreatedResponse(**response_data)

    def get_folders(self, search_name: Optional[str] = None) -> List[FolderItem]:
        """
        List all folders, optionally filtered by name

        Args:
            search_name: Optional substring to filter folder names

        Returns:
            List of FolderItem objects
        """
        params = {}
        if search_name:
            params["search_name"] = search_name

        response_data = self._request("GET", "/folders", params=params)
        folders_response = FoldersListResponse(**response_data)
        return folders_response.folders

    def get_folder_by_id(self, folder_id: str) -> FolderItem:
        """
        Get folder information including status and size

        Args:
            folder_id: Folder ID to retrieve

        Returns:
            FolderItem containing folder info, status, currentSize, historicalSize
        """
        response_data = self._request("GET", f"/folders/{folder_id}")
        return FolderItem(**response_data)

    def update_folder(self, folder_id: str, folder_name: str) -> UpdatedResponse:
        """
        Update folder name

        Args:
            folder_id: Folder ID to update
            folder_name: New folder name

        Returns:
            UpdatedResponse containing update confirmation
        """
        data = {"folder_name": folder_name}
        response_data = self._request("PUT", f"/folders/{folder_id}", json_data=data)
        return UpdatedResponse(**response_data)

    def delete_folder(self, folder_id: str) -> DeletedResponse:
        """
        Delete a folder and all its contents

        Args:
            folder_id: Folder ID to delete

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = self._request("DELETE", f"/folders/{folder_id}")
        return DeletedResponse(**response_data)

    # File Management Methods

    def upload_file(self, folder_id: str, file_path: str) -> FileUploadResponse:
        """
        Upload a file to a folder

        Args:
            folder_id: Folder ID to upload to
            file_path: Path to the file to upload

        Returns:
            FileUploadResponse containing upload confirmation and file info
        """
        import os

        filename = os.path.basename(file_path)
        with open(file_path, "rb") as file:
            files = {"file": (filename, file)}
            # For file uploads, we need to remove Content-Type header to let requests set it
            headers = {
                k: (
                    v
                    if isinstance(v, str)
                    else v.decode("utf-8") if isinstance(v, bytes) else str(v)
                )
                for k, v in self.session.headers.items()
                if k.lower() != "content-type"
            }
            response_data = self._request(
                "POST", f"/folders/{folder_id}/files", files=files, headers=headers
            )
            return FileUploadResponse(**response_data)

    def upload_file_from_url(
        self, folder_id: str, files: List[Dict[str, str]]
    ) -> FileUploadResponse:
        """
        Upload files from URLs to a folder

        Args:
            folder_id: Folder ID to upload to
            files: List of file dictionaries with url and optional filename

        Returns:
            FileUploadResponse containing upload confirmation and file info
        """
        data = {"files": files}
        response_data = self._request(
            "POST", f"/folders/{folder_id}/files/url", json_data=data
        )
        return FileUploadResponse(**response_data)

    def get_files(
        self, folder_id: str, search_name: Optional[str] = None
    ) -> List[FileItem]:
        """
        List files in a folder, optionally filtered by name

        Args:
            folder_id: Folder ID to list files from
            search_name: Optional substring to filter file names

        Returns:
            List of FileItem objects with file info
        """
        params = {}
        if search_name:
            params["search_name"] = search_name

        response_data = self._request(
            "GET", f"/folders/{folder_id}/files", params=params
        )
        files_response = FilesListResponse(**response_data)
        return files_response.files

    def get_file_by_id(self, folder_id: str, file_id: str) -> FileItem:
        """
        Get file information

        Args:
            folder_id: Folder ID containing the file
            file_id: File ID to retrieve

        Returns:
            FileItem containing file info
        """
        response_data = self._request("GET", f"/folders/{folder_id}/files/{file_id}")
        return FileItem(**response_data)

    def delete_file_by_id(self, folder_id: str, file_id: str) -> DeletedResponse:
        """
        Delete a specific file

        Args:
            folder_id: Folder ID containing the file
            file_id: File ID to delete

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = self._request("DELETE", f"/folders/{folder_id}/files/{file_id}")
        return DeletedResponse(**response_data)

    def delete_all_files(self, folder_id: str) -> DeletedResponse:
        """
        Delete all files in a folder

        Args:
            folder_id: Folder ID to delete all files from

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = self._request("DELETE", f"/folders/{folder_id}/files")
        return DeletedResponse(**response_data)

    # Chat Management Methods

    def create_chat(self, folder_id: str, openai_key: str) -> ChatCreatedResponse:
        """
        Create a new chat session for a folder

        Args:
            folder_id: Folder ID to create chat for
            openai_key: OpenAI API key for chat functionality

        Returns:
            ChatCreatedResponse containing creation confirmation with chat_id
        """
        request = ChatCreate(folder_id=folder_id, openai_key=openai_key)
        response_data = self._request("POST", "/chats", json_data=request.model_dump())
        return ChatCreatedResponse(**response_data)

    def get_chats(self, folder_id: Optional[str] = None) -> List[ChatItem]:
        """
        List chats, optionally filtered by folder

        Args:
            folder_id: Optional folder ID to filter chats

        Returns:
            List of ChatItem objects with chat info
        """
        params = {}
        if folder_id:
            params["folder_id"] = folder_id

        response_data = self._request("GET", "/chats", params=params)
        chats_response = ChatsListResponse(**response_data)
        return chats_response.chats

    def get_chat_by_id(self, chat_id: str) -> ChatItem:
        """
        Get chat information

        Args:
            chat_id: Chat ID to retrieve

        Returns:
            ChatItem containing chat info
        """
        response_data = self._request("GET", f"/chats/{chat_id}")
        return ChatItem(**response_data)

    def update_chat(self, chat_id: str, chat_name: str) -> UpdatedResponse:
        """
        Update chat name

        Args:
            chat_id: Chat ID to update
            chat_name: New chat name

        Returns:
            UpdatedResponse containing update confirmation
        """
        data = {"chat_name": chat_name}
        response_data = self._request("PUT", f"/chats/{chat_id}", json_data=data)
        return UpdatedResponse(**response_data)

    def delete_chat(self, chat_id: str) -> DeletedResponse:
        """
        Delete a chat and all its asks

        Args:
            chat_id: Chat ID to delete

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = self._request("DELETE", f"/chats/{chat_id}")
        return DeletedResponse(**response_data)

    # Ask Management Methods (Core RAG Functionality)

    def submit_ask(
        self,
        chat_id: str,
        query: str,
        is_qna: bool = True,
        citation_style: Optional[str] = None,
        file_sources: Optional[List[str]] = None,
    ) -> AskItem:
        """
        Submit a question to get RAG response

        Args:
            chat_id: Chat ID to submit question to
            query: Question/query to ask
            is_qna: If True, returns final answer + sources. If False, returns sources only.
            citation_style: Optional citation style for sources
            file_sources: Optional list of specific files to query against

        Returns:
            AskItem containing ask response with answer and sources
        """
        request = AskSubmitRequest(
            query=query,
            is_qna=is_qna,
            citation_style=citation_style,
            file_sources=file_sources,
        )
        response_data = self._request(
            "POST", f"/chats/{chat_id}/asks", json_data=request.model_dump()
        )
        return AskItem(**response_data)

    def get_asks(self, chat_id: str, msg_maxlen: int = 120) -> List[AskItem]:
        """
        List all asks in a chat with truncated content

        Args:
            chat_id: Chat ID to list asks from
            msg_maxlen: Maximum length of truncated query and response content

        Returns:
            List of AskItem objects with truncated content
        """
        params = {"msg_maxlen": msg_maxlen}
        response_data = self._request("GET", f"/chats/{chat_id}/asks", params=params)
        asks_response = AsksListResponse(**response_data)
        return asks_response.asks

    def get_ask_by_index(
        self,
        chat_id: str,
        ask_index: int,
        show_files: bool = False,
        show_source: bool = False,
    ) -> AskItem:
        """
        Get specific ask with full content and optional metadata

        Args:
            chat_id: Chat ID containing the ask
            ask_index: Index of the ask in the chat
            show_files: Whether to include list of files checked for response
            show_source: Whether to include source data for response

        Returns:
            AskItem containing full ask info with optional files and source data
        """
        params = {}
        if show_files:
            params["show_files"] = "true"
        if show_source:
            params["show_source"] = "true"

        response_data = self._request(
            "GET", f"/chats/{chat_id}/asks/{ask_index}", params=params
        )
        return AskItem(**response_data)

    def delete_ask_by_index(self, chat_id: str, ask_index: int) -> DeletedResponse:
        """
        Delete a specific ask by index

        Args:
            chat_id: Chat ID containing the ask
            ask_index: Index of the ask to delete

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = self._request("DELETE", f"/chats/{chat_id}/asks/{ask_index}")
        return DeletedResponse(**response_data)

    # Convenience Methods

    def get_folder_file_count(self, folder_id: str) -> int:
        """
        Get the number of files in a folder

        Args:
            folder_id: Folder ID to count files for

        Returns:
            Number of files in the folder
        """
        files = self.get_files(folder_id)
        return len(files)

    def get_chat_ask_count(self, chat_id: str) -> int:
        """
        Get the number of asks in a chat

        Args:
            chat_id: Chat ID to count asks for

        Returns:
            Number of asks in the chat
        """
        asks = self.get_asks(chat_id)
        return len(asks)
