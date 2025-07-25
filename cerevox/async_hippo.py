"""
Cerevox SDK's Asynchronous Hippo Client for RAG Operations
"""

import asyncio
import base64
import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp

from .exceptions import (
    LexaAuthError,
    LexaError,
    LexaTimeoutError,
    create_error_from_response,
)
from .models import (
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
)

FAILED_ID = "Failed to get request ID from response"

logger = logging.getLogger(__name__)


class AsyncHippo:
    """
    Official Asynchronous Python Client for Cerevox Hippo (RAG Operations)

    This client provides a clean, Pythonic async interface to the Cerevox RAG API,
    supporting folder management, file uploads, chat creation, and AI-powered
    question answering on your documents.

    Example:
        >>> async with AsyncHippo(email="user@example.com", api_key="password") as client:
        ...     # Client automatically authenticates during context entry
        ...     # Create folder and upload files
        ...     await client.create_folder("docs", "My Documents")
        ...     await client.upload_file("docs", "/path/to/document.pdf")
        ...     # Create chat and ask questions
        ...     chat = await client.create_chat("docs", "your-openai-key")
        ...     response = await client.submit_ask(chat["chat_id"], "What is this document about?")
        ...     print(response["response"])

    Happy RAG Processing! 🔍 ✨
    """

    def __init__(
        self,
        *,
        email: str,
        api_key: str,
        base_url: str = "https://dev.cerevox.ai/v1",
        max_retries: int = 3,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the AsyncHippo client

        Args:
            email: User email address for authentication
            api_key: User password for authentication
            base_url: Base URL for the Cerevox RAG API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
            **kwargs: Additional aiohttp ClientSession arguments
        """
        self.email = email
        self.api_key = api_key
        if not self.email or not self.api_key:
            raise ValueError("Both email and api_key are required for authentication")

        # Validate base_url format
        if not base_url or not isinstance(base_url, str):
            raise ValueError("base_url must be a non-empty string")

        # Basic URL validation
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            raise ValueError("base_url must start with http:// or https://")

        # Validate max_retries
        if not isinstance(max_retries, int):
            raise TypeError("max_retries must be an integer")
        if max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")

        self.base_url = base_url.rstrip("/")  # Remove trailing slash
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries

        # Session configuration
        self.session_kwargs = {
            "timeout": self.timeout,
            "headers": {
                "User-Agent": "cerevox-python-async/0.1.6",
                "Content-Type": "application/json",
            },
            **kwargs,
        }

        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "AsyncHippo":
        """Async context manager entry"""
        await self.start_session()
        # Automatically authenticate using email and password
        await self.login(self.email, self.api_key)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Async context manager exit"""
        await self.close_session()

    async def start_session(self) -> None:
        """Start the aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(**self.session_kwargs)

    async def close_session(self) -> None:
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[aiohttp.FormData] = None,
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
            data: FormData for file uploads
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the API

        Raises:
            LexaAuthError: If authentication fails
            LexaError: If the request fails for other reasons
            LexaTimeoutError: If the request times out
            Various other LexaError subclasses: Based on response status and content
        """
        if not self.session:
            raise LexaError("Session not initialized. Use async context manager.")

        url = f"{self.base_url}{endpoint}"

        # Merge additional headers
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)

        # For file uploads, remove Content-Type to let aiohttp set it
        if data is not None:
            request_headers = {
                k: v for k, v in request_headers.items() if k.lower() != "content-type"
            }

        request_kwargs = {
            "params": params,
            "headers": request_headers,
            **kwargs,
        }

        if json_data is not None:
            request_kwargs["json"] = json_data
        elif data is not None:
            request_kwargs["data"] = data

        try:
            async with self.session.request(method, url, **request_kwargs) as response:
                # Extract request ID for error reporting
                request_id = response.headers.get("x-request-id", FAILED_ID)

                # Handle successful responses
                if 200 <= response.status < 300:
                    try:
                        response_data: Dict[str, Any] = await response.json()
                        return response_data
                    except (ValueError, aiohttp.ContentTypeError):
                        # Non-JSON response, return basic success info
                        return {"status": "success"}

                # Handle error responses
                try:
                    error_data = await response.json()
                except (ValueError, aiohttp.ContentTypeError):
                    error_text = await response.text()
                    error_data = {
                        "error": f"HTTP {response.status}",
                        "message": error_text,
                    }

                # Create and raise appropriate exception
                raise create_error_from_response(
                    status_code=response.status,
                    response_data=error_data,
                    request_id=request_id,
                )

        except asyncio.TimeoutError as e:
            logger.error(f"Request timeout for {method} {url}: {e}")
            raise LexaTimeoutError(
                "Request timed out", timeout_duration=self.timeout.total
            ) from e

        except aiohttp.ClientError as e:
            logger.error(f"Request failed for {method} {url}: {e}")
            raise LexaError(f"Request failed: {e}", request_id=FAILED_ID) from e

    # Authentication Methods

    async def login(self, email: str, password: str) -> TokenResponse:
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

        # Update session headers temporarily for login
        if self.session:
            self.session.headers.update(
                {"Authorization": f"Basic {encoded_credentials}"}
            )

        response_data = await self._request("POST", "/token/login")

        token_response = TokenResponse(**response_data)

        # Update session headers with Bearer token
        if self.session:
            self.session.headers.update(
                {"Authorization": f"Bearer {token_response.access_token}"}
            )

        return token_response

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: The refresh token

        Returns:
            TokenResponse with new tokens
        """
        request = TokenRefreshRequest(refresh_token=refresh_token)
        response_data = await self._request(
            "POST", "/token/refresh", json_data=request.model_dump()
        )
        token_response = TokenResponse(**response_data)

        # Update session headers with new Bearer token
        if self.session:
            self.session.headers.update(
                {"Authorization": f"Bearer {token_response.access_token}"}
            )

        return token_response

    async def revoke_token(self) -> MessageResponse:
        """
        Revoke the current access token

        Returns:
            MessageResponse with revocation confirmation
        """
        response_data = await self._request("POST", "/token/revoke")
        return MessageResponse(**response_data)

    # Folder Management Methods

    async def create_folder(self, folder_id: str, folder_name: str) -> Dict[str, Any]:
        """
        Create a new folder for document organization

        Args:
            folder_id: Unique identifier for the folder
            folder_name: Display name for the folder

        Returns:
            Dict containing creation confirmation with folder_id and folder_name
        """
        data = {"folder_id": folder_id, "folder_name": folder_name}
        return await self._request("POST", "/folders", json_data=data)

    async def get_folders(
        self, search_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all folders, optionally filtered by name

        Args:
            search_name: Optional substring to filter folder names

        Returns:
            List of folder dictionaries with folder_id and folder_name
        """
        params = {}
        if search_name:
            params["search_name"] = search_name

        response_data = await self._request("GET", "/folders", params=params)
        return response_data.get("folders", [])

    async def get_folder_by_id(self, folder_id: str) -> Dict[str, Any]:
        """
        Get folder information including status and size

        Args:
            folder_id: Folder ID to retrieve

        Returns:
            Dict containing folder info, status, currentSize, historicalSize
        """
        return await self._request("GET", f"/folders/{folder_id}")

    async def update_folder(self, folder_id: str, folder_name: str) -> Dict[str, Any]:
        """
        Update folder name

        Args:
            folder_id: Folder ID to update
            folder_name: New folder name

        Returns:
            Dict containing update confirmation
        """
        data = {"folder_name": folder_name}
        return await self._request("PUT", f"/folders/{folder_id}", json_data=data)

    async def delete_folder(self, folder_id: str) -> Dict[str, Any]:
        """
        Delete a folder and all its contents

        Args:
            folder_id: Folder ID to delete

        Returns:
            Dict containing deletion confirmation
        """
        return await self._request("DELETE", f"/folders/{folder_id}")

    # File Management Methods

    async def upload_file(self, folder_id: str, file_path: str) -> Dict[str, Any]:
        """
        Upload a file to a folder

        Args:
            folder_id: Folder ID to upload to
            file_path: Path to the file to upload

        Returns:
            Dict containing upload confirmation and file info
        """
        import os

        filename = os.path.basename(file_path)

        # Create FormData for file upload
        data = aiohttp.FormData()
        with open(file_path, "rb") as file:
            data.add_field("file", file, filename=filename)

            return await self._request("POST", f"/folders/{folder_id}/files", data=data)

    async def upload_file_from_url(
        self, folder_id: str, files: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Upload files from URLs to a folder

        Args:
            folder_id: Folder ID to upload to
            files: List of file dictionaries with url and optional filename

        Returns:
            Dict containing upload confirmation and file info
        """
        data = {"files": files}
        return await self._request(
            "POST", f"/folders/{folder_id}/files/url", json_data=data
        )

    async def get_files(
        self, folder_id: str, search_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in a folder, optionally filtered by name

        Args:
            folder_id: Folder ID to list files from
            search_name: Optional substring to filter file names

        Returns:
            List of file dictionaries with file info
        """
        params = {}
        if search_name:
            params["search_name"] = search_name

        response_data = await self._request(
            "GET", f"/folders/{folder_id}/files", params=params
        )
        return response_data.get("files", [])

    async def get_file_by_id(self, folder_id: str, file_id: str) -> Dict[str, Any]:
        """
        Get file information

        Args:
            folder_id: Folder ID containing the file
            file_id: File ID to retrieve

        Returns:
            Dict containing file info
        """
        return await self._request("GET", f"/folders/{folder_id}/files/{file_id}")

    async def delete_file_by_id(self, folder_id: str, file_id: str) -> Dict[str, Any]:
        """
        Delete a specific file

        Args:
            folder_id: Folder ID containing the file
            file_id: File ID to delete

        Returns:
            Dict containing deletion confirmation
        """
        return await self._request("DELETE", f"/folders/{folder_id}/files/{file_id}")

    async def delete_all_files(self, folder_id: str) -> Dict[str, Any]:
        """
        Delete all files in a folder

        Args:
            folder_id: Folder ID to delete all files from

        Returns:
            Dict containing deletion confirmation
        """
        return await self._request("DELETE", f"/folders/{folder_id}/files")

    # Chat Management Methods

    async def create_chat(self, folder_id: str, openai_key: str) -> Dict[str, Any]:
        """
        Create a new chat session for a folder

        Args:
            folder_id: Folder ID to create chat for
            openai_key: OpenAI API key for chat functionality

        Returns:
            Dict containing creation confirmation with chat_id
        """
        data = {"folder_id": folder_id, "openai_key": openai_key}
        return await self._request("POST", "/chats", json_data=data)

    async def get_chats(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List chats, optionally filtered by folder

        Args:
            folder_id: Optional folder ID to filter chats

        Returns:
            List of chat dictionaries with chat info
        """
        params = {}
        if folder_id:
            params["folder_id"] = folder_id

        response_data = await self._request("GET", "/chats", params=params)
        return response_data.get("chats", [])

    async def get_chat_by_id(self, chat_id: str) -> Dict[str, Any]:
        """
        Get chat information

        Args:
            chat_id: Chat ID to retrieve

        Returns:
            Dict containing chat info
        """
        return await self._request("GET", f"/chats/{chat_id}")

    async def update_chat(self, chat_id: str, chat_name: str) -> Dict[str, Any]:
        """
        Update chat name

        Args:
            chat_id: Chat ID to update
            chat_name: New chat name

        Returns:
            Dict containing update confirmation
        """
        data = {"chat_name": chat_name}
        return await self._request("PUT", f"/chats/{chat_id}", json_data=data)

    async def delete_chat(self, chat_id: str) -> Dict[str, Any]:
        """
        Delete a chat and all its asks

        Args:
            chat_id: Chat ID to delete

        Returns:
            Dict containing deletion confirmation
        """
        return await self._request("DELETE", f"/chats/{chat_id}")

    # Ask Management Methods (Core RAG Functionality)

    async def submit_ask(
        self, chat_id: str, query: str, file_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Submit a question to get RAG response

        Args:
            chat_id: Chat ID to submit question to
            query: Question/query to ask
            file_sources: Optional list of specific files to query against

        Returns:
            Dict containing ask response with answer and sources
        """
        data = {"query": query}
        if file_sources:
            data["file_sources"] = file_sources

        return await self._request("POST", f"/chats/{chat_id}/asks", json_data=data)

    async def get_asks(
        self, chat_id: str, msg_maxlen: int = 120
    ) -> List[Dict[str, Any]]:
        """
        List all asks in a chat with truncated content

        Args:
            chat_id: Chat ID to list asks from
            msg_maxlen: Maximum length of truncated query and response content

        Returns:
            List of ask dictionaries with truncated content
        """
        params = {"msg_maxlen": msg_maxlen}
        response_data = await self._request(
            "GET", f"/chats/{chat_id}/asks", params=params
        )
        return response_data.get("asks", [])

    async def get_ask_by_index(
        self,
        chat_id: str,
        ask_index: int,
        show_files: bool = False,
        show_source: bool = False,
    ) -> Dict[str, Any]:
        """
        Get specific ask with full content and optional metadata

        Args:
            chat_id: Chat ID containing the ask
            ask_index: Index of the ask in the chat
            show_files: Whether to include list of files checked for response
            show_source: Whether to include source data for response

        Returns:
            Dict containing full ask info with optional files and source data
        """
        params = {}
        if show_files:
            params["show_files"] = "true"
        if show_source:
            params["show_source"] = "true"

        return await self._request(
            "GET", f"/chats/{chat_id}/asks/{ask_index}", params=params
        )

    async def delete_ask_by_index(self, chat_id: str, ask_index: int) -> Dict[str, Any]:
        """
        Delete a specific ask by index

        Args:
            chat_id: Chat ID containing the ask
            ask_index: Index of the ask to delete

        Returns:
            Dict containing deletion confirmation
        """
        return await self._request("DELETE", f"/chats/{chat_id}/asks/{ask_index}")

    # Convenience Methods

    async def get_folder_file_count(self, folder_id: str) -> int:
        """
        Get the number of files in a folder

        Args:
            folder_id: Folder ID to count files for

        Returns:
            Number of files in the folder
        """
        files = await self.get_files(folder_id)
        return len(files)

    async def get_chat_ask_count(self, chat_id: str) -> int:
        """
        Get the number of asks in a chat

        Args:
            chat_id: Chat ID to count asks for

        Returns:
            Number of asks in the chat
        """
        asks = await self.get_asks(chat_id)
        return len(asks)
