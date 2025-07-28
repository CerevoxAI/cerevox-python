"""
Cerevox SDK's Asynchronous Hippo Client for RAG Operations
"""

import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp

from ..core.async_base_client import AsyncBaseClient
from ..core.models import (
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
    UpdatedResponse,
)

logger = logging.getLogger(__name__)


class AsyncHippo(AsyncBaseClient):
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
        email: Optional[str] = None,
        api_key: Optional[str] = None,
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
        super().__init__(
            email=email,
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            **kwargs,
        )

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
        Override base _request to support file uploads with FormData
        """
        if data is not None:
            # For file uploads, remove Content-Type to let aiohttp set it
            upload_headers = {
                k: v for k, v in (headers or {}).items() if k.lower() != "content-type"
            }
            return await super()._request(
                method=method,
                endpoint=endpoint,
                params=params,
                headers=upload_headers,
                data=data,
                **kwargs,
            )
        else:
            return await super()._request(
                method=method,
                endpoint=endpoint,
                json_data=json_data,
                params=params,
                headers=headers,
                **kwargs,
            )

    # Authentication Methods (inherited from AsyncBaseClient)

    # Folder Management Methods

    async def create_folder(
        self, folder_id: str, folder_name: str
    ) -> FolderCreatedResponse:
        """
        Create a new folder for document organization

        Args:
            folder_id: Unique identifier for the folder
            folder_name: Display name for the folder

        Returns:
            FolderCreatedResponse containing creation confirmation
        """
        request = FolderCreate(folder_id=folder_id, folder_name=folder_name)
        response_data = await self._request(
            "POST", "/folders", json_data=request.model_dump()
        )
        return FolderCreatedResponse(**response_data)

    async def get_folders(self, search_name: Optional[str] = None) -> List[FolderItem]:
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

        response_data = await self._request("GET", "/folders", params=params)
        folders_response = FoldersListResponse(**response_data)
        return folders_response.folders

    async def get_folder_by_id(self, folder_id: str) -> FolderItem:
        """
        Get folder information including status and size

        Args:
            folder_id: Folder ID to retrieve

        Returns:
            FolderItem containing folder info, status, currentSize, historicalSize
        """
        response_data = await self._request("GET", f"/folders/{folder_id}")
        return FolderItem(**response_data)

    async def update_folder(self, folder_id: str, folder_name: str) -> UpdatedResponse:
        """
        Update folder name

        Args:
            folder_id: Folder ID to update
            folder_name: New folder name

        Returns:
            UpdatedResponse containing update confirmation
        """
        data = {"folder_name": folder_name}
        response_data = await self._request(
            "PUT", f"/folders/{folder_id}", json_data=data
        )
        return UpdatedResponse(**response_data)

    async def delete_folder(self, folder_id: str) -> DeletedResponse:
        """
        Delete a folder and all its contents

        Args:
            folder_id: Folder ID to delete

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = await self._request("DELETE", f"/folders/{folder_id}")
        return DeletedResponse(**response_data)

    # File Management Methods

    async def upload_file(self, folder_id: str, file_path: str) -> FileUploadResponse:
        """
        Upload a file to a folder

        Args:
            folder_id: Folder ID to upload to
            file_path: Path to the file to upload

        Returns:
            FileUploadResponse containing upload confirmation and file info
        """

        filename = os.path.basename(file_path)

        # Create FormData for file upload
        data = aiohttp.FormData()
        with open(file_path, "rb") as file:
            data.add_field("file", file, filename=filename)

            response_data = await self._request(
                "POST", f"/folders/{folder_id}/files", data=data
            )
            return FileUploadResponse(**response_data)

    async def upload_file_from_url(
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
        response_data = await self._request(
            "POST", f"/folders/{folder_id}/files/url", json_data=data
        )
        return FileUploadResponse(**response_data)

    async def get_files(
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

        response_data = await self._request(
            "GET", f"/folders/{folder_id}/files", params=params
        )
        files_response = FilesListResponse(**response_data)
        return files_response.files

    async def get_file_by_id(self, folder_id: str, file_id: str) -> FileItem:
        """
        Get file information

        Args:
            folder_id: Folder ID containing the file
            file_id: File ID to retrieve

        Returns:
            FileItem containing file info
        """
        response_data = await self._request(
            "GET", f"/folders/{folder_id}/files/{file_id}"
        )
        return FileItem(**response_data)

    async def delete_file_by_id(self, folder_id: str, file_id: str) -> DeletedResponse:
        """
        Delete a specific file

        Args:
            folder_id: Folder ID containing the file
            file_id: File ID to delete

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = await self._request(
            "DELETE", f"/folders/{folder_id}/files/{file_id}"
        )
        return DeletedResponse(**response_data)

    async def delete_all_files(self, folder_id: str) -> DeletedResponse:
        """
        Delete all files in a folder

        Args:
            folder_id: Folder ID to delete all files from

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = await self._request("DELETE", f"/folders/{folder_id}/files")
        return DeletedResponse(**response_data)

    # Chat Management Methods

    async def create_chat(self, folder_id: str, openai_key: str) -> ChatCreatedResponse:
        """
        Create a new chat session for a folder

        Args:
            folder_id: Folder ID to create chat for
            openai_key: OpenAI API key for chat functionality

        Returns:
            ChatCreatedResponse containing creation confirmation with chat_id
        """
        request = ChatCreate(folder_id=folder_id, openai_key=openai_key)
        response_data = await self._request(
            "POST", "/chats", json_data=request.model_dump()
        )
        return ChatCreatedResponse(**response_data)

    async def get_chats(self, folder_id: Optional[str] = None) -> List[ChatItem]:
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

        response_data = await self._request("GET", "/chats", params=params)
        chats_response = ChatsListResponse(**response_data)
        return chats_response.chats

    async def get_chat_by_id(self, chat_id: str) -> ChatItem:
        """
        Get chat information

        Args:
            chat_id: Chat ID to retrieve

        Returns:
            ChatItem containing chat info
        """
        response_data = await self._request("GET", f"/chats/{chat_id}")
        return ChatItem(**response_data)

    async def update_chat(self, chat_id: str, chat_name: str) -> UpdatedResponse:
        """
        Update chat name

        Args:
            chat_id: Chat ID to update
            chat_name: New chat name

        Returns:
            UpdatedResponse containing update confirmation
        """
        data = {"chat_name": chat_name}
        response_data = await self._request("PUT", f"/chats/{chat_id}", json_data=data)
        return UpdatedResponse(**response_data)

    async def delete_chat(self, chat_id: str) -> DeletedResponse:
        """
        Delete a chat and all its asks

        Args:
            chat_id: Chat ID to delete

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = await self._request("DELETE", f"/chats/{chat_id}")
        return DeletedResponse(**response_data)

    # Ask Management Methods (Core RAG Functionality)

    async def submit_ask(
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
        response_data = await self._request(
            "POST", f"/chats/{chat_id}/asks", json_data=request.model_dump()
        )
        return AskItem(**response_data)

    async def get_asks(self, chat_id: str, msg_maxlen: int = 120) -> List[AskItem]:
        """
        List all asks in a chat with truncated content

        Args:
            chat_id: Chat ID to list asks from
            msg_maxlen: Maximum length of truncated query and response content

        Returns:
            List of AskItem objects with truncated content
        """
        params = {"msg_maxlen": msg_maxlen}
        response_data = await self._request(
            "GET", f"/chats/{chat_id}/asks", params=params
        )
        asks_response = AsksListResponse(**response_data)
        return asks_response.asks

    async def get_ask_by_index(
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

        response_data = await self._request(
            "GET", f"/chats/{chat_id}/asks/{ask_index}", params=params
        )
        return AskItem(**response_data)

    async def delete_ask_by_index(
        self, chat_id: str, ask_index: int
    ) -> DeletedResponse:
        """
        Delete a specific ask by index

        Args:
            chat_id: Chat ID containing the ask
            ask_index: Index of the ask to delete

        Returns:
            DeletedResponse containing deletion confirmation
        """
        response_data = await self._request(
            "DELETE", f"/chats/{chat_id}/asks/{ask_index}"
        )
        return DeletedResponse(**response_data)

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
