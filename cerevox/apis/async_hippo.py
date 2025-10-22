"""
Cerevox SDK's Asynchronous Hippo Client for RAG Operations
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

import aiohttp

from ..core import (
    AskItem,
    AskListItem,
    AsksListResponse,
    AskSubmitRequest,
    AskSubmitResponse,
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
    ProcessingMode,
    ReasoningLevel,
    ResponseType,
    UpdatedResponse,
)
from ..services import AsyncIngest

logger = logging.getLogger(__name__)


class AsyncHippo(AsyncIngest):
    """
    Official Asynchronous Python Client for Cerevox Hippo RAG Operations.

    This client provides a comprehensive, async-first interface to the Cerevox
    Retrieval-Augmented Generation (RAG) API, enabling document ingestion,
    semantic search, and AI-powered question answering on your document
    collections. The client supports folder-based organization, multiple file
    formats, and conversational AI interactions.

    Examples
    --------
    Basic usage with context manager (recommended):

    >>> async with AsyncHippo(api_key="your_token") as client:
    ...     # Create a folder for documents
    ...     folder = await client.create_folder("research", "Research Papers")
    ...
    ...     # Upload documents
    ...     upload_result = await client.upload_file("research", "/path/to/paper.pdf")
    ...
    ...     # Create a chat session
    ...     chat = await client.create_chat("research")
    ...
    ...     # Ask questions about the documents
    ...     response = await client.submit_ask(
    ...         chat.chat_id,
    ...         "What are the main findings in this research?"
    ...     )
    ...     print(response.response)

    Batch document processing:

    >>> async with AsyncHippo(api_key="your_token") as client:
    ...     # Upload multiple files from URLs
    ...     files = [
    ...         {"url": "https://example.com/doc1.pdf", "filename": "doc1.pdf"},
    ...         {"url": "https://example.com/doc2.pdf", "filename": "doc2.pdf"}
    ...     ]
    ...     await client.upload_file_from_url("research", files)
    ...
    ...     # Get folder statistics
    ...     file_count = await client.get_folder_file_count("research")
    ...     print(f"Uploaded {file_count} files")

    Advanced RAG queries with citations:

    >>> async with AsyncHippo(api_key="your_token") as client:
    ...     response = await client.submit_ask(
    ...         chat_id="chat123",
    ...         query="Summarize the methodology section",
    ...         citation_style="APA",
    ...         sources=["specific_file_id"]
    ...     )

    Notes
    -----
    This client is designed for async/await usage and should be used within
    an async context manager to ensure proper resource cleanup. All methods
    are coroutines and must be awaited.

    File uploads support common document formats including PDF, DOCX, TXT,
    HTML, and various image formats.

    RAG responses include source citations and confidence scores to help
    verify the reliability of generated answers.

    Happy RAG Processing! 🔍 ✨
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://dev.cerevox.ai/v1",
        data_url: str = "https://data.cerevox.ai",
        max_retries: int = 3,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the AsyncHippo client for RAG operations.

        Parameters
        ----------
        api_key : str, optional
            User Personal Access Token (PAT) for authentication. If None,
            attempts to read from CEREVOX_API_KEY environment variable.
        base_url : str, default "https://dev.cerevox.ai/v1"
            Base URL for cerevox requests.
        data_url : str, default "https://data.cerevox.ai"
            Data URL for the Cerevox RAG API. Change to production URL
            for live environments.
        max_retries : int, default 3
            Maximum retry attempts for failed requests. Must be >= 0.
        timeout : float, default 30.0
            Default request timeout in seconds. File uploads automatically
            use extended timeouts based on file size.
        **kwargs : dict
            Additional aiohttp.ClientSession configuration including
            connector, trust_env, proxy, or SSL settings.

        Raises
        ------
        LexaAuthError
            If authentication fails due to invalid API key or network issues.

        Notes
        -----
        The client automatically handles authentication during initialization
        and maintains session state for optimal performance. Use within an
        async context manager for proper resource management.
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            data_url=data_url,
            product="hippo",
            max_retries=max_retries,
            timeout=timeout,
            **kwargs,
        )

    # Folder Management Methods

    async def create_folder(
        self, folder_id: str, folder_name: str
    ) -> FolderCreatedResponse:
        """
        Create a new folder for document organization and RAG operations.

        Parameters
        ----------
        folder_id : str
            Unique identifier for the folder. Must be alphanumeric with
            optional underscores and hyphens. Used in API endpoints.
        folder_name : str
            Human-readable display name for the folder. Can contain
            spaces and special characters.

        Returns
        -------
        FolderCreatedResponse
            Object containing creation confirmation with folder metadata
            including creation timestamp and initial status.

        Notes
        -----
        Folders serve as logical containers for document collections and
        enable scoped RAG operations. Each folder maintains its own vector
        embeddings and search indices for optimal performance.
        """
        request = FolderCreate(folder_id=folder_id, folder_name=folder_name)
        response_data = await self._request(
            "POST", "/folders", json_data=request.model_dump()
        )
        return FolderCreatedResponse(**response_data)

    async def get_folders(self, search_name: Optional[str] = None) -> List[FolderItem]:
        """
        Retrieve list of folders with optional name filtering.

        Parameters
        ----------
        search_name : str, optional
            Substring to filter folder names. Case-insensitive partial
            matching is performed on folder_name field.

        Returns
        -------
        List[FolderItem]
            List of folder objects containing folder_id, folder_name,
            creation timestamp, current size, and processing status.

        Notes
        -----
        Folder sizes include all ingested documents and generated embeddings.
        Historical size tracking allows monitoring of growth over time.
        """
        params = {}
        if search_name:
            params["search_name"] = search_name

        response_data = await self._request("GET", "/folders", params=params)
        folders_response = FoldersListResponse(**response_data)
        return folders_response.folders

    async def get_folder_by_id(self, folder_id: str) -> FolderItem:
        """
        Retrieve detailed information for a specific folder.

        Parameters
        ----------
        folder_id : str
            The unique folder identifier to retrieve information for.

        Returns
        -------
        FolderItem
            Folder object containing complete metadata including folder_id,
            folder_name, creation timestamp, current size, historical size,
            processing status, and file count.

        Notes
        -----
        Folder status indicates processing state: 'ready', 'processing',
        'error', or 'empty'. Only folders in 'ready' state support
        full RAG functionality.
        """
        response_data = await self._request("GET", f"/folders/{folder_id}")
        return FolderItem(**response_data)

    async def update_folder(self, folder_id: str, folder_name: str) -> UpdatedResponse:
        """
        Update the display name of an existing folder.

        Parameters
        ----------
        folder_id : str
            The unique folder identifier to update.
        folder_name : str
            New display name for the folder. Must be non-empty and
            within length limits (1-255 characters).

        Returns
        -------
        UpdatedResponse
            Object containing update confirmation and timestamp of
            the modification operation.

        Notes
        -----
        Updating folder names does not affect folder_id or any associated
        documents, embeddings, or chat sessions. Only the display name
        is modified.
        """
        data = {"folder_name": folder_name}
        response_data = await self._request(
            "PUT", f"/folders/{folder_id}", json_data=data
        )
        return UpdatedResponse(**response_data)

    async def delete_folder(self, folder_id: str) -> DeletedResponse:
        """
        Delete a folder and all its contents permanently.

        Parameters
        ----------
        folder_id : str
            The unique folder identifier to delete.

        Returns
        -------
        DeletedResponse
            Object containing deletion confirmation and cleanup status
            for all associated resources.

        Notes
        -----
        This is a destructive operation that cannot be undone. All documents,
        embeddings, vector indices, chat sessions, and conversation history
        associated with the folder will be permanently removed.

        Active processing operations or open chat sessions may prevent
        deletion. Ensure all operations are complete before deletion.
        """
        response_data = await self._request("DELETE", f"/folders/{folder_id}")
        return DeletedResponse(**response_data)

    # File Management Methods

    async def upload_file(self, folder_id: str, file_path: str) -> FileUploadResponse:
        """
        Upload a local file to a folder for RAG processing.

        Parameters
        ----------
        folder_id : str
            The folder identifier to upload the file to. Folder must exist
            and be in a ready state.
        file_path : str
            Local filesystem path to the file. File must be readable and
            within size limits (max 100MB).

        Returns
        -------
        FileUploadResponse
            Object containing upload confirmation, file metadata, and
            processing status including file_id for future operations.

        Notes
        -----
        Supported file formats include: PDF, DOCX, DOC, TXT, HTML, RTF,
        PPTX, XLSX, CSV, MD, and various image formats (PNG, JPG, TIFF).

        Files are automatically processed for text extraction, chunking,
        and vector embedding generation. Processing time varies based on
        file size and complexity.

        Large files may take several minutes to process completely before
        becoming available for RAG operations.
        """

        filename = os.path.basename(file_path)

        # Create FormData for file upload
        data = aiohttp.FormData()
        data.add_field("file", open(file_path, "rb"), filename=filename)
        form_data = data._gen_form_data()
        content_type = form_data.content_type

        headers = {"Content-Type": content_type}

        response_data = await self._request(
            "POST", f"/folders/{folder_id}/files", data=data, headers=headers
        )
        return FileUploadResponse(**response_data)

    async def upload_file_from_url(
        self, folder_id: str, files: List[Dict[str, str]]
    ) -> FileUploadResponse:
        """
        Upload files from URLs to a folder for RAG processing.

        Parameters
        ----------
        folder_id : str
            The folder identifier to upload files to. Folder must exist
            and be accessible.
        files : List[Dict[str, str]]
            List of file dictionaries, each containing 'url' (required)
            and optionally 'filename' for custom naming. URLs must be
            publicly accessible.

        Returns
        -------
        FileUploadResponse
            Object containing upload confirmation, batch processing status,
            and metadata for all successfully uploaded files.

        Examples
        --------
        Upload from public URLs:

        >>> files = [
        ...     {"url": "https://example.com/report.pdf"},
        ...     {"url": "https://docs.example.com/manual.docx", "filename": "user_manual.docx"}
        ... ]
        >>> response = await client.upload_file_from_url("research", files)
        >>> print(f"Uploaded {len(response.files)} files")

        Upload research papers from repository:

        >>> arxiv_papers = [
        ...     {"url": "https://arxiv.org/pdf/2301.00001.pdf", "filename": "transformer_paper.pdf"},
        ...     {"url": "https://arxiv.org/pdf/2301.00002.pdf", "filename": "attention_paper.pdf"}
        ... ]
        >>> await client.upload_file_from_url("ai_research", arxiv_papers)

        Notes
        -----
        URLs must point to publicly accessible files without authentication
        requirements. The service will attempt to detect file types from
        content headers and URL extensions.

        If 'filename' is not provided, it will be inferred from the URL.
        Custom filenames help with organization and identification.

        This method is ideal for ingesting content from websites, repositories,
        or shared document platforms that provide direct download links.
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
        List files in a folder with optional name filtering.

        Parameters
        ----------
        folder_id : str
            The folder identifier to list files from.
        search_name : str, optional
            Substring to filter file names. Case-insensitive partial
            matching is performed on filename.

        Returns
        -------
        List[FileItem]
            List of file objects containing file_id, filename, upload
            timestamp, file size, processing status, and metadata.

        Raises
        ------
        LexaAuthError
            If authentication fails or lacks access to the folder.

        Examples
        --------
        List all files in a folder:

        >>> files = await client.get_files("research")
        >>> for file in files:
        ...     print(f"{file.filename} - {file.status}")

        Search for specific files:

        >>> pdf_files = await client.get_files("research", search_name=".pdf")
        >>> print(f"Found {len(pdf_files)} PDF files")

        Check processing status:

        >>> files = await client.get_files("research")
        >>> processing = [f for f in files if f.status == "processing"]
        >>> ready = [f for f in files if f.status == "ready"]
        >>> print(f"{len(ready)} ready, {len(processing)} processing")

        Notes
        -----
        File status indicates processing state: 'ready', 'processing',
        'error', or 'failed'. Only files in 'ready' state are available
        for RAG operations.

        Processing times vary based on file size, format complexity, and
        current system load. Text extraction and embedding generation
        occur automatically after upload.
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
        Retrieve detailed information for a specific file.

        Parameters
        ----------
        folder_id : str
            The folder identifier containing the file.
        file_id : str
            The unique file identifier to retrieve information for.

        Returns
        -------
        FileItem
            File object containing complete metadata including filename,
            file size, upload timestamp, processing status, error details
            if applicable, and content metadata.

        Raises
        ------
        LexaAuthError
            If authentication fails or lacks access to the file.
        """
        response_data = await self._request(
            "GET", f"/folders/{folder_id}/files/{file_id}"
        )
        return FileItem(**response_data)

    async def delete_file_by_id(self, folder_id: str, file_id: str) -> DeletedResponse:
        """
        Delete a specific file from a folder.

        Parameters
        ----------
        folder_id : str
            The folder identifier containing the file.
        file_id : str
            The unique file identifier to delete.

        Returns
        -------
        DeletedResponse
            Object containing deletion confirmation and cleanup status
            for associated embeddings and indices.

        Raises
        ------
        LexaAuthError
            If authentication fails or lacks deletion permissions.

        Notes
        -----
        This operation permanently removes the file and all associated
        vector embeddings from the RAG system. The file will no longer
        be available for search or chat operations.

        Files cannot be deleted while processing. Wait for processing
        to complete before attempting deletion.
        """
        response_data = await self._request(
            "DELETE", f"/folders/{folder_id}/files/{file_id}"
        )
        return DeletedResponse(**response_data)

    async def delete_all_files(self, folder_id: str) -> DeletedResponse:
        """
        Delete all files in a folder permanently.

        Parameters
        ----------
        folder_id : str
            The folder identifier to delete all files from.

        Returns
        -------
        DeletedResponse
            Object containing deletion confirmation and cleanup status
            for all files and associated resources.

        Raises
        ------
        LexaAuthError
            If authentication fails or lacks deletion permissions.

        Examples
        --------
        >>> response = await client.delete_all_files("temp_folder")
        >>> print(f"All files deleted: {response.success}")

        Safe bulk deletion:

        >>> folder = await client.get_folder_by_id("temp_folder")
        >>> if folder.status == "ready":
        ...     await client.delete_all_files("temp_folder")

        Notes
        -----
        This is a destructive operation that cannot be undone. All files,
        embeddings, and vector indices in the folder will be permanently
        removed, but the folder structure itself will remain.

        This operation may take time to complete for folders with many
        files or large embeddings. Consider deleting individual files
        for more granular control.
        """
        response_data = await self._request("DELETE", f"/folders/{folder_id}/files")
        return DeletedResponse(**response_data)

    # Chat Management Methods

    async def create_chat(self, folder_id: str) -> ChatCreatedResponse:
        """
        Create a new chat session for RAG operations on a folder.

        Parameters
        ----------
        folder_id : str
            The folder identifier to create a chat session for. Folder
            must exist and contain processed files.

        Returns
        -------
        ChatCreatedResponse
            Object containing chat creation confirmation with chat_id
            and initial session metadata.

        Raises
        ------
        NotFoundError
            If the specified folder_id does not exist.
        ValidationError
            If the folder is empty or has no processed files available
            for RAG operations.
        LexaAuthError
            If authentication fails or lacks chat creation permissions.

        Examples
        --------
        >>> chat = await client.create_chat("research")
        >>> print(f"Created chat: {chat.chat_id}")

        Create chat after file upload:

        >>> await client.upload_file("research", "document.pdf")
        >>> # Wait for processing to complete
        >>> chat = await client.create_chat("research")

        Notes
        -----
        Chat sessions maintain conversation context and enable follow-up
        questions with memory of previous interactions. Each chat is
        scoped to a specific folder's document collection.

        Folders must contain at least one processed file in 'ready' status
        before chat sessions can be created.
        """
        request = ChatCreate(folder_id=folder_id)
        response_data = await self._request(
            "POST", "/chats", json_data=request.model_dump()
        )
        return ChatCreatedResponse(**response_data)

    async def get_chats(self, folder_id: Optional[str] = None) -> List[ChatItem]:
        """
        List chat sessions with optional folder filtering.

        Parameters
        ----------
        folder_id : str, optional
            Folder identifier to filter chats. If None, returns all
            accessible chat sessions.

        Returns
        -------
        List[ChatItem]
            List of chat objects containing chat_id, folder_id, creation
            timestamp, last activity, and chat session metadata.

        Raises
        ------
        LexaAuthError
            If authentication fails or session has expired.

        Notes
        -----
        Chat sessions persist until explicitly deleted and maintain full
        conversation history including questions, answers, and sources.

        Inactive chat sessions remain available indefinitely but may have
        reduced performance for very old conversations.
        """
        params = {}
        if folder_id:
            params["folder_id"] = folder_id

        response_data = await self._request("GET", "/chats", params=params)
        chats_response = ChatsListResponse(**response_data)
        return chats_response.chats

    async def get_chat_by_id(self, chat_id: str) -> ChatItem:
        """
        Retrieve detailed information for a specific chat session.

        Parameters
        ----------
        chat_id : str
            The unique chat identifier to retrieve information for.

        Returns
        -------
        ChatItem
            Chat object containing complete metadata including chat_id,
            associated folder_id, creation timestamp, last activity,
            total questions asked, and session status.

        Raises
        ------
        NotFoundError
            If the specified chat_id does not exist.
        LexaAuthError
            If authentication fails or lacks access to the chat.

        Notes
        -----
        Chat metadata includes usage statistics and activity tracking
        to help manage and organize conversation sessions effectively.
        """
        response_data = await self._request("GET", f"/chats/{chat_id}")
        return ChatItem(**response_data)

    async def update_chat(self, chat_id: str, chat_name: str) -> UpdatedResponse:
        """
        Update the display name of a chat session.

        Parameters
        ----------
        chat_id : str
            The unique chat identifier to update.
        chat_name : str
            New display name for the chat session. Must be non-empty
            and within length limits.

        Returns
        -------
        UpdatedResponse
            Object containing update confirmation and modification timestamp.

        Notes
        -----
        Updating chat names helps with organization and identification
        of conversation sessions but does not affect the conversation
        history or functionality.
        """
        data = {"chat_name": chat_name}
        response_data = await self._request("PUT", f"/chats/{chat_id}", json_data=data)
        return UpdatedResponse(**response_data)

    async def delete_chat(self, chat_id: str) -> DeletedResponse:
        """
        Delete a chat session and all its conversation history.

        Parameters
        ----------
        chat_id : str
            The unique chat identifier to delete.

        Returns
        -------
        DeletedResponse
            Object containing deletion confirmation and cleanup status
            for all conversation data.

        Raises
        ------
        NotFoundError
            If the specified chat_id does not exist.
        LexaAuthError
            If authentication fails or lacks deletion permissions.

        Examples
        --------
        >>> response = await client.delete_chat("chat123")
        >>> print(f"Chat deleted: {response.success}")

        Clean up old chats:

        >>> from datetime import datetime, timedelta
        >>> cutoff_date = datetime.now() - timedelta(days=30)
        >>> chats = await client.get_chats()
        >>> for chat in chats:
        ...     if chat.last_activity < cutoff_date:
        ...         await client.delete_chat(chat.chat_id)

        Notes
        -----
        This operation permanently removes the chat session and all
        associated conversation history including questions, answers,
        and source citations. This cannot be undone.

        Deleting a chat does not affect the underlying documents or
        folder, only the conversation session.
        """
        response_data = await self._request("DELETE", f"/chats/{chat_id}")
        return DeletedResponse(**response_data)

    # Ask Management Methods (Core RAG Functionality)

    async def submit_ask(
        self,
        chat_id: str,
        query: str,
        response_type: Union[ResponseType, str] = ResponseType.ANSWERS,
        citation_style: Optional[str] = None,
        source_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        answer_options: Optional[Dict[str, str]] = None,
        reasoning_level: Union[ReasoningLevel, str] = ReasoningLevel.NONE,
        include_retrieval: bool = False,
        mode: str = "lite",
    ) -> AskSubmitResponse:
        """
        Submit a question to get AI-powered RAG responses from documents.

        Parameters
        ----------
        chat_id : str
            The chat session identifier to submit the question to.
        query : str
            The question or query to ask about the documents. Can be
            natural language questions, requests for summaries, or
            specific information retrieval.
        response_type : Union[ResponseType, str], default ResponseType.ANSWERS
            Type of response to return. Either 'answers' for AI-generated answer
            with source citations, or 'sources' for only relevant source passages
            without AI interpretation.
        citation_style : str, optional
            Citation format for sources. Options include "APA", "MLA",
            "Chicago", or custom formats. Defaults to standard format.
        source_ids : List[str], optional
            List of specific file IDs to limit the search scope. If None,
            searches all files in the associated folder.
        top_k : int, optional
            Number of top relevant passages to retrieve (1-100 inclusive).
            Controls the maximum number of document chunks returned for
            generating the response. Higher values provide more context
            but may increase processing time.
        answer_options : Dict[str, str], optional
            Multiple choice answer options (e.g., {'A': 'option1', 'B': 'option2'}).
        reasoning_level : Union[ReasoningLevel, str], default ReasoningLevel.NONE
            Level of reasoning to include in the response. Options: 'none', 'basic',
            or 'detailed'.
        include_retrieval : bool, default False
            Whether the answer_options should be included in the retrieval process.
        mode : str, default "lite"
            Query processing mode. Either 'lite' for faster processing or 'pro'
            for more comprehensive analysis.

        Returns
        -------
        AskSubmitResponse
            Object containing the AI response, source citations, confidence
            scores, and metadata about the retrieval process.

        Raises
        ------
        NotFoundError
            If the specified chat_id does not exist or has no associated files.
        ValidationError
            If query is empty or citation_style is not supported.
        RateLimitError
            If request rate limits are exceeded.
        LexaAuthError
            If authentication fails or lacks query permissions.

        Examples
        --------
        Basic question answering:

        >>> response = await client.submit_ask(
        ...     "chat123",
        ...     "What are the main conclusions of this research?"
        ... )
        >>> print(response.response)
        >>> for source in response.sources:
        ...     print(f"Source: {source.filename}")

        Get source passages only:

        >>> response = await client.submit_ask(
        ...     "chat123",
        ...     "methodology section",
        ...     response_type=ResponseType.SOURCES
        ... )
        >>> for passage in response.sources:
        ...     print(passage.content)

        Targeted search with citations and reasoning:

        >>> response = await client.submit_ask(
        ...     "chat123",
        ...     "What is the experimental design?",
        ...     citation_style="APA",
        ...     source_ids=["file123", "file456"],
        ...     reasoning_level=ReasoningLevel.DETAILED
        ... )

        Follow-up questions:

        >>> # Initial question
        >>> response1 = await client.submit_ask("chat123", "What is the main topic?")
        >>>
        >>> # Follow-up with context
        >>> response2 = await client.submit_ask(
        ...     "chat123",
        ...     "Can you elaborate on the methodology mentioned earlier?"
        ... )

        Notes
        -----
        RAG responses combine retrieved relevant passages with AI generation
        to provide accurate, contextual answers. Source citations enable
        verification of information and deeper investigation.

        Chat context is maintained across questions, enabling natural
        follow-up conversations and references to previous answers.

        Response quality depends on document content, query specificity,
        and the semantic similarity between question and document passages.
        """

        # Convert string to enum if necessary
        response_type_enum = (
            ResponseType(response_type)
            if isinstance(response_type, str)
            else response_type
        )
        reasoning_level_enum = (
            ReasoningLevel(reasoning_level)
            if isinstance(reasoning_level, str)
            else reasoning_level
        )

        request = AskSubmitRequest(
            query=query,
            response_type=response_type_enum,
            citation_style=citation_style,
            source_ids=source_ids,
            top_k=top_k,
            answer_options=answer_options,
            reasoning_level=reasoning_level_enum,
            include_retrieval=include_retrieval,
            mode=mode,
        )
        response_data = await self._request(
            "POST",
            f"/chats/{chat_id}/asks",
            json_data=request.model_dump(exclude_none=True),
            timeout=300.0,
        )
        return AskSubmitResponse(**response_data)

    async def get_asks(self, chat_id: str, msg_maxlen: int = 120) -> List[AskListItem]:
        """
        Retrieve conversation history with truncated content for overview.

        Parameters
        ----------
        chat_id : str
            The chat session identifier to retrieve conversation history from.
        msg_maxlen : int, default 120
            Maximum character length for truncated query and response content.
            Used for quick overview of conversation flow.

        Returns
        -------
        List[AskListItem]
            List of conversation items with truncated queries and responses,
            timestamps, and basic metadata for browsing conversation history.


        Examples
        --------
        Browse conversation history:

        >>> asks = await client.get_asks("chat123")
        >>> for i, ask in enumerate(asks):
        ...     print(f"{i}: {ask.query_truncated}")
        ...     print(f"   Answer: {ask.response_truncated}")

        Find specific conversations:

        >>> asks = await client.get_asks("chat123", msg_maxlen=200)
        >>> methodology_asks = [
        ...     ask for ask in asks
        ...     if "methodology" in ask.query_truncated.lower()
        ... ]

        Notes
        -----
        This method provides a quick overview of conversation flow without
        loading full content. Use get_ask_by_index() to retrieve complete
        questions and answers for specific interactions.

        Conversation items are ordered chronologically from oldest to newest.
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
        Retrieve complete information for a specific conversation item.

        Parameters
        ----------
        chat_id : str
            The chat session identifier containing the conversation.
        ask_index : int
            Zero-based index of the conversation item to retrieve.
            Use negative indices to count from the end (-1 for latest).
        show_files : bool, default False
            Whether to include the list of files that were searched
            to generate the response.
        show_source : bool, default False
            Whether to include the raw source passages and vector
            similarity scores used in generation.

        Returns
        -------
        AskItem
            Complete conversation item with full query, response, source
            citations, and optional detailed metadata.

        Raises
        ------
        NotFoundError
            If the chat_id does not exist or ask_index is out of range.
        LexaAuthError
            If authentication fails or lacks access to the conversation.

        Examples
        --------
        Get the latest conversation:

        >>> latest_ask = await client.get_ask_by_index("chat123", -1)
        >>> print(f"Question: {latest_ask.query}")
        >>> print(f"Answer: {latest_ask.response}")

        Detailed analysis with source data:

        >>> ask = await client.get_ask_by_index(
        ...     "chat123", 0,
        ...     show_files=True,
        ...     show_source=True
        ... )
        >>> print(f"Files searched: {len(ask.files_searched)}")
        >>> for source in ask.source_passages:
        ...     print(f"Similarity: {source.similarity_score}")

        Review specific conversation:

        >>> asks_list = await client.get_asks("chat123")
        >>> for i, ask_summary in enumerate(asks_list):
        ...     if "important topic" in ask_summary.query_truncated:
        ...         full_ask = await client.get_ask_by_index("chat123", i)
        ...         print(full_ask.response)

        Notes
        -----
        This method retrieves complete conversation data including full
        text, source citations, and optional debugging information for
        understanding RAG retrieval and generation processes.

        The show_source option provides transparency into the similarity
        scores and passage selection that influenced the AI response.
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
        Delete a specific conversation item from chat history.

        Parameters
        ----------
        chat_id : str
            The chat session identifier containing the conversation.
        ask_index : int
            Zero-based index of the conversation item to delete.

        Returns
        -------
        DeletedResponse
            Object containing deletion confirmation and cleanup status.

        Raises
        ------
        NotFoundError
            If the chat_id does not exist or ask_index is out of range.
        LexaAuthError
            If authentication fails or lacks deletion permissions.

        Examples
        --------
        >>> response = await client.delete_ask_by_index("chat123", 0)
        >>> print(f"Conversation item deleted: {response.success}")

        Remove erroneous questions:

        >>> asks = await client.get_asks("chat123")
        >>> for i, ask in enumerate(asks):
        ...     if "test" in ask.query_truncated.lower():
        ...         await client.delete_ask_by_index("chat123", i)

        Notes
        -----
        This operation removes the specific question-answer pair from
        the conversation history. It does not affect other conversations
        or the underlying document collection.

        Deleting conversation items may affect chat context for subsequent
        questions if they referenced the deleted content.
        """
        response_data = await self._request(
            "DELETE", f"/chats/{chat_id}/asks/{ask_index}"
        )
        return DeletedResponse(**response_data)

    # Convenience Methods

    async def get_folder_file_count(self, folder_id: str) -> int:
        """
        Get the total number of files in a folder.

        Parameters
        ----------
        folder_id : str
            The folder identifier to count files for.

        Returns
        -------
        int
            Total number of files in the folder, regardless of
            processing status.
        """
        files = await self.get_files(folder_id)
        return len(files)

    async def get_chat_ask_count(self, chat_id: str) -> int:
        """
        Get the total number of questions in a chat session.

        Parameters
        ----------
        chat_id : str
            The chat session identifier to count questions for.

        Returns
        -------
        int
            Total number of questions asked in the chat session.
        """
        asks = await self.get_asks(chat_id)
        return len(asks)
