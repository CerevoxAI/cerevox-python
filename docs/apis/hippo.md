# Hippo API Reference

## Table of Contents

- [AsyncHippo](#asynchippo)
  - [Constructor](#constructor)
  - [Folder Methods](#folder-methods)
    - [create\_folder(folder\_id, folder\_name)](#create_folderfolder_id-folder_name)
    - [get\_folders(\*\*options)](#get_foldersoptions)
    - [get\_folder\_by\_id(folder\_id)](#get_folder_by_idfolder_id)
    - [update\_folder(folder\_id, folder\_name)](#update_folderfolder_id-folder_name)
    - [delete\_folder(folder\_id)](#delete_folderfolder_id)
  - [File Methods](#file-methods)
    - [upload\_file(folder\_id, file\_path)](#upload_filefolder_id-file_path)
    - [upload\_file\_from\_url(folder\_id, files)](#upload_file_from_urlfolder_id-files)
    - [get\_folder\_file\_count(folder\_id)](#get_folder_file_countfolder_id)
    - [get\_files(folder\_id, \*\*options)](#get_filesfolder_id-options)
    - [get\_file\_by\_id(folder\_id, file\_id)](#get_file_by_idfolder_id-file_id)
    - [delete\_file\_by\_id(folder\_id, file\_id)](#delete_file_by_idfolder_id-file_id)
    - [delete\_all\_files(folder\_id)](#delete_all_filesfolder_id)
  - [Chat Methods](#chat-methods)
    - [create\_chat(folder\_id)](#create_chatfolder_id)
    - [get\_chats(\*\*options)](#get_chatsoptions)
    - [get\_chat\_by\_id(chat\_id)](#get_chat_by_idchat_id)
    - [update\_chat(chat\_id, chat\_name)](#update_chatchat_id-chat_name)
    - [delete\_chat(chat\_id)](#delete_chatchat_id)
  - [Ask Methods](#ask-methods)
    - [submit\_ask(chat\_id, query, \*\*options)](#submit_askchat_id-query-options)
    - [get\_chat\_ask\_count(chat\_id: str)](#get_chat_ask_countchat_id-str)
    - [get\_asks(chat\_id, \*\*options)](#get_askschat_id-options)
    - [get\_ask\_by\_index(chat\_id, ask\_index, \*\*options)](#get_ask_by_indexchat_id-ask_index-options)
    - [delete\_ask\_by\_index(chat\_id, ask\_index)](#delete_ask_by_indexchat_id-ask_index)
- [Hippo](#hippo)
  - [Constructor](#constructor-1)
  - [Folder Methods](#folder-methods-1)
    - [create\_folder(folder\_id, folder\_name)](#create_folderfolder_id-folder_name-1)
    - [get\_folders(\*\*options)](#get_foldersoptions-1)
    - [get\_folder\_by\_id(folder\_id)](#get_folder_by_idfolder_id-1)
    - [update\_folder(folder\_id, folder\_name)](#update_folderfolder_id-folder_name-1)
    - [delete\_folder(folder\_id)](#delete_folderfolder_id-1)
  - [File Methods](#file-methods-1)
    - [upload\_file(folder\_id, file\_path)](#upload_filefolder_id-file_path-1)
    - [upload\_file\_from\_url(folder\_id, files)](#upload_file_from_urlfolder_id-files-1)
    - [get\_folder\_file\_count(folder\_id)](#get_folder_file_countfolder_id-1)
    - [get\_files(folder\_id, \*\*options)](#get_filesfolder_id-options-1)
    - [get\_file\_by\_id(folder\_id, file\_id)](#get_file_by_idfolder_id-file_id-1)
    - [delete\_file\_by\_id(folder\_id, file\_id)](#delete_file_by_idfolder_id-file_id-1)
    - [delete\_all\_files(folder\_id)](#delete_all_filesfolder_id-1)
  - [Chat Methods](#chat-methods-1)
    - [create\_chat(folder\_id)](#create_chatfolder_id-1)
    - [get\_chats(\*\*options)](#get_chatsoptions-1)
    - [get\_chat\_by\_id(chat\_id)](#get_chat_by_idchat_id-1)
    - [update\_chat(chat\_id, chat\_name)](#update_chatchat_id-chat_name-1)
    - [delete\_chat(chat\_id)](#delete_chatchat_id-1)
  - [Ask Methods](#ask-methods-1)
    - [submit\_ask(chat\_id, query, \*\*options)](#submit_askchat_id-query-options-1)
    - [get\_chat\_ask\_count(chat\_id: str)](#get_chat_ask_countchat_id-str-1)
    - [get\_asks(chat\_id, \*\*options)](#get_askschat_id-options-1)
    - [get\_ask\_by\_index(chat\_id, ask\_index, \*\*options)](#get_ask_by_indexchat_id-ask_index-options-1)
    - [delete\_ask\_by\_index(chat\_id, ask\_index)](#delete_ask_by_indexchat_id-ask_index-1)

---

## AsyncHippo

Official Asynchronous Python Client for Cerevox Hippo (RAG Operations)

### Constructor

```python
AsyncHippo(email: str, api_key: str, **options)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `email` | str | Yes | - | User email address for authentication |
| `api_key` | str | Yes | - | Your Cerevox API key for above email |
| `base_url` | str | No | (Cerevox Base Url) | Base URL for the Cerevox Hippo API |
| `max_retries` | int | No | 3 | Maximum retry attempts for failed requests |
| `timeout` | float | No | 30.0 | Request timeout in seconds |

### Folder Methods

#### create_folder(folder_id, folder_name)

Create a new folder for document organization.

```python
created = await client.create_folder(
    folder_id="new-folder-id",
    folder_name="My Document Folders"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the new folder. |
| `folder_name` | str | Yes | - | Display name for the new folder |

**Returns:** `FolderCreatedResponse` - Confirmation of folder creation

#### get_folders(**options)

List all folders, optionally filtered by name.

```python
folders = await client.get_folders(
    search_name="Documents"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_name` | str | No | None | Optional substring to filter folder names. If provided, only folders containing this substring will be returned |

**Returns:** `List[FolderItem]` - List of FolderItem objects

#### get_folder_by_id(folder_id)

Get folder information including status and size.

```python
folder = await client.get_folder_by_id(
    folder_id="folder-123"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to retrieve |

**Returns:** `FolderItem` - FolderItem object with folder info

#### update_folder(folder_id, folder_name)

Update folder name.

```python
updated = await client.update_folder(
    folder_id="folder-123",
    folder_name="My New Folder Name"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to update |
| `folder_name` | str | Yes | - | New display name for the folder |

**Returns:** `UpdatedResponse` - Confirmation of folder update

#### delete_folder(folder_id)

Delete a folder and all its contents.

```python
deleted = await client.delete_folder(
    folder_id="folder-123"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to delete |

**Returns:** `DeletedResponse` - Confirmation of folder deletion

### File Methods

#### upload_file(folder_id, file_path)

Upload a file to a folder.

```python
upload_resp = await client.upload_file(
    folder_id="folder-123",
    file_path="/path/to/file.pdf"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to upload to |
| `file_path` | str | Yes | - | Path to the file to upload |

**Returns:** `FileUploadResponse` - Confirmation of file upload and metadata

#### upload_file_from_url(folder_id, files)
Upload files from URLs to a folder.

```python
upload_resp = await client.upload_file_from_url(
    folder_id="folder-123",
    files=[
        {
            "url": "https://example.com/file1.pdf",
            "filename": "file1.pdf"
        },
        {
            "url": "https://example.com/file2.docx",
            "filename": "file2.docx"
        }
    ]
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to upload to |
| `files` | List[Dict] | Yes | [] | List of file dictionaries with url and optional filename |

**Returns:** `FileUploadResponse` - Confirmation of file upload and metadata

#### get_folder_file_count(folder_id)

Get the number of files in a folder.

```python
file_count = await client.get_folder_file_count(
    folder_id="folder-123"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to count files for |

**Returns:** `int` - Number of files in the folder

#### get_files(folder_id, **options)

List files in a folder, optionally filtered by name.

```python
files = await client.get_files(
    folder_id="folder-123",
    search_name="Revenue"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to list files from |
| `search_name` | str | No | None | Optional substring to filter file names |

**Returns:** `List[FileItem]` - List of FileItem objects with file info

#### get_file_by_id(folder_id, file_id)

Get file information.

```python
file = await client.get_file_by_id(
    folder_id="folder-123",
    file_id="file-456"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder containing the file |
| `file_id` | str | Yes | - | Unique identifier for the file to retrieve |

**Returns:** `FileItem` - File information

#### delete_file_by_id(folder_id, file_id)

Delete a specific file.

```python
deleted = await client.delete_file_by_id(
    folder_id="folder-123",
    file_id="file-456"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder containing the file |
| `file_id` | str | Yes | - | Unique identifier for the file to delete |

**Returns:** `DeletedResponse` - Confirmation of file deletion

#### delete_all_files(folder_id)

Delete all files in a folder.

```python
deleted = await client.delete_all_files(
    folder_id="folder-123"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to delete all files from |

**Returns:** `DeletedResponse` - Confirmation of file deletion

### Chat Methods

#### create_chat(folder_id)

Create a new chat session for a folder.

```python
new_chat = await client.create_chat(
    folder_id="folder-123"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | Yes | - | Unique identifier for the folder to create chat for |

**Returns:** `ChatCreatedResponse` - Confirmation of chat creation with chat ID

#### get_chats(**options)

List chats, optionally filtered by folder.

```python
chats = await client.get_chats(
    folder_id="folder-123"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_id` | str | No | None | Optional folder ID to filter chats. If not provided, all chats will be returned |

**Returns:** `List[ChatItem]` - List of ChatItem objects with chat information

#### get_chat_by_id(chat_id)

Get chat information.

```python
chat = await client.get_chat_by_id(
    chat_id="chat-456"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat_id` | str | Yes | - | Unique identifier for the chat to retrieve |

**Returns:** `ChatItem` - Chat information

#### update_chat(chat_id, chat_name)

Update chat name.

```python
updated = await client.update_chat(
    chat_id="chat-456",
    chat_name="New Chat Name"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat_id` | str | Yes | - | Unique identifier for the chat to update |
| `chat_name` | str | Yes | - | New display name for the chat |

**Returns:** `UpdatedResponse` - Confirmation of chat update

#### delete_chat(chat_id)

Delete a chat and all its asks.

```python
deleted = await client.delete_chat(
    chat_id="chat-456"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat_id` | str | Yes | - | Unique identifier for the chat to delete |

**Returns:** `DeletedResponse` - Confirmation of chat deletion

### Ask Methods

#### submit_ask(chat_id, query, **options)

Submit a question to get RAG response.

```python
response = await client.submit_ask(
    chat_id="chat-456",
    query="What is the capital of France?"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat_id` | str | Yes | - | Unique identifier for the chat to submit question to |
| `query` | str | Yes | - | Question or query to ask |
| `is_qna` | bool | No | True | If True, returns final answer + sources. If False, returns sources only |
| `citation_style` | str | No | None | Optional citation style for sources |
| `sources` | List[str] | No | None | Optional list of specific files to query against |

**Returns:** `AskSubmitResponse` - Response with answer and sources

#### get_chat_ask_count(chat_id: str)

Get the number of asks in a chat.

```python
ask_count = await client.get_chat_ask_count(
    chat_id="chat-456"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat_id` | str | Yes | - | Unique identifier for the chat to count asks for |

**Returns:** `int` - Number of asks in the chat

#### get_asks(chat_id, **options)

List all asks in a chat with truncated content.

```python
asks = await client.get_asks(
    chat_id="chat-456",
    msg_maxlen=180
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat_id` | str | Yes | - | Unique identifier for the chat to list asks from |
| `msg_maxlen` | int | No | 120 | Maximum length of truncated query and response content |

**Returns:** `List[AskListItem]` - List of AskListItem objects with truncated content

#### get_ask_by_index(chat_id, ask_index, **options)

Get specific ask with full content and optional metadata.

```python
ask = await client.get_ask_by_index(
    chat_id="chat-456",
    ask_index=0,
    show_files=True,
    show_source=True
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat_id` | str | Yes | - | Unique identifier for the chat containing the ask |
| `ask_index` | int | Yes | - | Index of the ask in the chat |
| `show_files` | bool | No | False | Whether to include list of files checked for response |
| `show_source` | bool | No | False | Whether to include source data for response |

**Returns:** `AskItem` - Ask item containing full ask info with optional files and source data

#### delete_ask_by_index(chat_id, ask_index)

Delete a specific ask by index.

```python
deleted = await client.delete_ask_by_index(
    chat_id="chat-456",
    ask_index=0
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `chat_id` | str | Yes | - | Unique identifier for the chat containing the ask |
| `ask_index` | int | Yes | - | Index of the ask to delete |

**Returns:** `DeletedResponse` - Confirmation of ask deletion

---

## Hippo

Synchronous client for document processing (legacy/compatibility).

### Constructor

```python
Hippo(email: str, api_key: str, **options)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `email` | str | Yes | - | User email address for authentication |
| `api_key` | str | Yes | - | Your Cerevox API key for above email |
| `base_url` | str | No | (Cerevox Base Url) | Base URL for the Cerevox Hippo API |
| `max_retries` | int | No | 3 | Maximum retry attempts for failed requests |
| `timeout` | float | No | 30.0 | Request timeout in seconds |

### Folder Methods

#### create_folder(folder_id, folder_name)

Create a new folder for document organization.

**Parameters:** Same as AsyncHippo.create_folder()

**Returns:** `FolderCreatedResponse` - Confirmation of folder creation

#### get_folders(**options)

List all folders, optionally filtered by name.

**Parameters:** Same as AsyncHippo.get_folders()

**Returns:** `List[FolderItem]` - List of FolderItem objects

#### get_folder_by_id(folder_id)

Get folder information including status and size.

**Parameters:** Same as AsyncHippo.get_folder_by_id()

**Returns:** `FolderItem` - FolderItem object with folder info

#### update_folder(folder_id, folder_name)

Update folder name.

**Parameters:** Same as AsyncHippo.update_folder()

**Returns:** `UpdatedResponse` - Confirmation of folder update

#### delete_folder(folder_id)

Delete a folder and all its contents.

**Parameters:** Same as AsyncHippo.delete_folder()

**Returns:** `DeletedResponse` - Confirmation of folder deletion

### File Methods

#### upload_file(folder_id, file_path)

Upload a file to a folder.

**Parameters:** Same as AsyncHippo.upload_file()

**Returns:** `FileUploadResponse` - Confirmation of file upload and metadata

#### upload_file_from_url(folder_id, files)
Upload files from URLs to a folder.

**Parameters:** Same as AsyncHippo.upload_file_from_url()

**Returns:** `FileUploadResponse` - Confirmation of file upload and metadata

#### get_folder_file_count(folder_id)

Get the number of files in a folder.

**Parameters:** Same as AsyncHippo.get_folder_file_count()

**Returns:** `int` - Number of files in the folder

#### get_files(folder_id, **options)

List files in a folder, optionally filtered by name.

**Parameters:** Same as AsyncHippo.get_files()

**Returns:** `List[FileItem]` - List of FileItem objects with file info

#### get_file_by_id(folder_id, file_id)

Get file information.

**Parameters:** Same as AsyncHippo.get_file_by_id()

**Returns:** `FileItem` - File information

#### delete_file_by_id(folder_id, file_id)

Delete a specific file.

**Parameters:** Same as AsyncHippo.delete_file_by_id()

**Returns:** `DeletedResponse` - Confirmation of file deletion

#### delete_all_files(folder_id)

Delete all files in a folder.

**Parameters:** Same as AsyncHippo.delete_all_files()

**Returns:** `DeletedResponse` - Confirmation of file deletion

### Chat Methods

#### create_chat(folder_id)

Create a new chat session for a folder.

**Parameters:** Same as AsyncHippo.create_chat()

**Returns:** `ChatCreatedResponse` - Confirmation of chat creation with chat ID

#### get_chats(**options)

List chats, optionally filtered by folder.

**Parameters:** Same as AsyncHippo.get_chats()

**Returns:** `List[ChatItem]` - List of ChatItem objects with chat information

#### get_chat_by_id(chat_id)

Get chat information.

**Parameters:** Same as AsyncHippo.get_chat_by_id()

**Returns:** `ChatItem` - Chat information

#### update_chat(chat_id, chat_name)

Update chat name.

**Parameters:** Same as AsyncHippo.update_chat()

**Returns:** `UpdatedResponse` - Confirmation of chat update

#### delete_chat(chat_id)

Delete a chat and all its asks.

**Parameters:** Same as AsyncHippo.delete_chat()

**Returns:** `DeletedResponse` - Confirmation of chat deletion

### Ask Methods

#### submit_ask(chat_id, query, **options)

Submit a question to get RAG response.

**Parameters:** Same as AsyncHippo.submit_ask()

**Returns:** `AskSubmitResponse` - Response with answer and sources

#### get_chat_ask_count(chat_id: str)

Get the number of asks in a chat.

**Parameters:** Same as AsyncHippo.get_chat_ask_count()

**Returns:** `int` - Number of asks in the chat

#### get_asks(chat_id, **options)

List all asks in a chat with truncated content.

**Parameters:** Same as AsyncHippo.get_asks()

**Returns:** `List[AskListItem]` - List of AskListItem objects with truncated content

#### get_ask_by_index(chat_id, ask_index, **options)

Get specific ask with full content and optional metadata.

**Parameters:** Same as AsyncHippo.get_ask_by_index()

**Returns:** `AskItem` - Ask item containing full ask info with optional files and source data

#### delete_ask_by_index(chat_id, ask_index)

Delete a specific ask by index.

**Parameters:** Same as AsyncHippo.delete_ask_by_index()

**Returns:** `DeletedResponse` - Confirmation of ask deletion