# Lexa API Reference

## Table of Contents

- [AsyncLexa](#asynclexa)
  - [Constructor](#constructor)
  - [Methods](#methods)
    - [parse(files, \*\*options)](#parsefiles-options)
    - [parse\_urls(urls, \*\*options)](#parse_urlsurls-options)
    - [list\_s3\_buckets()](#list_s3_buckets)
    - [list\_s3\_folders(bucket\_name)](#list_s3_foldersbucket_name)
    - [parse\_s3\_folder(bucket\_name, folder\_path, \*\*options)](#parse_s3_folderbucket_name-folder_path-options)
    - [list\_box\_folders()](#list_box_folders)
    - [parse\_box\_folder(box\_folder\_id, \*\*options)](#parse_box_folderbox_folder_id-options)
    - [list\_dropbox\_folders()](#list_dropbox_folders)
    - [parse\_dropbox\_folder(folder\_path, \*\*options)](#parse_dropbox_folderfolder_path-options)
    - [list\_sharepoint\_sites()](#list_sharepoint_sites)
    - [list\_sharepoint\_drives(site\_id)](#list_sharepoint_drivessite_id)
    - [list\_sharepoint\_folders(drive\_id)](#list_sharepoint_foldersdrive_id)
    - [parse\_sharepoint\_folder(drive\_id, folder\_id, \*\*options)](#parse_sharepoint_folderdrive_id-folder_id-options)
    - [list\_salesforce\_folders()](#list_salesforce_folders)
    - [parse\_salesforce\_folder(folder\_name, \*\*options)](#parse_salesforce_folderfolder_name-options)
    - [parse\_sendme\_files(ticket)](#parse_sendme_filesticket)
- [Lexa](#lexa)
  - [Constructor](#constructor-1)
  - [Methods](#methods-1)
    - [parse(files, \*\*options)](#parsefiles-options-1)
    - [parse\_urls(urls, \*\*options)](#parse_urlsurls-options-1)
    - [list\_s3\_buckets()](#list_s3_buckets-1)
    - [list\_s3\_folders(bucket\_name)](#list_s3_foldersbucket_name-1)
    - [parse\_s3\_folder(bucket\_name, folder\_path, \*\*options)](#parse_s3_folderbucket_name-folder_path-options-1)
    - [list\_box\_folders()](#list_box_folders-1)
    - [parse\_box\_folder(box\_folder\_id, \*\*options)](#parse_box_folderbox_folder_id-options-1)
    - [list\_dropbox\_folders()](#list_dropbox_folders-1)
    - [parse\_dropbox\_folder(folder\_path, \*\*options)](#parse_dropbox_folderfolder_path-options-1)
    - [list\_sharepoint\_sites()](#list_sharepoint_sites-1)
    - [list\_sharepoint\_drives(site\_id)](#list_sharepoint_drivessite_id-1)
    - [list\_sharepoint\_folders(drive\_id)](#list_sharepoint_foldersdrive_id-1)
    - [parse\_sharepoint\_folder(drive\_id, folder\_id, \*\*options)](#parse_sharepoint_folderdrive_id-folder_id-options-1)
    - [list\_salesforce\_folders()](#list_salesforce_folders-1)
    - [parse\_salesforce\_folder(folder\_name, \*\*options)](#parse_salesforce_folderfolder_name-options-1)
    - [parse\_sendme\_files(ticket)](#parse_sendme_filesticket-1)

---

## AsyncLexa

The main async client for document processing with enterprise-grade reliability.

### Constructor

```python
AsyncLexa(api_key: str, **options)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | str | Yes | - | Your Cerevox API key from [cerevox.ai/lexa](https://cerevox.ai/lexa) |
| `base_url` | str | No | (Cerevox Base URL) | Base URL of the Cerevox API |
| `max_concurrent` | int | No | 10 | Maximum number of concurrent processing jobs |
| `timeout` | float | No | 60.0 | Request timeout in seconds |
| `max_retries` | int | No | 3 | Maximum retry attempts for failed requests |

### Methods

#### parse(files, **options)

Parse documents from local files or file paths.

```python
documents = await client.parse(
    files=["path/to/file.pdf", "document.docx"],
    progress_callback=callback_fn,
    mode="DEFAULT"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `files` | List[str] | Yes | - | List of file paths to parse |
| `mode` | str | No | "DEFAULT" | Processing mode: "DEFAULT" or "ADVANCED" |
| `max_poll_time` | float | No | - | Maximum time to wait for completion |
| `poll_interval` | float | No | - | Time between status checks |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `show_progress` | bool | No | False | Whether to show a progress bar using tqdm |

**Returns:** `DocumentBatch` - Collection of parsed documents

#### parse_urls(urls, **options)

Parse documents from URLs.

```python
documents = await client.parse_urls(
    urls=["https://example.com/doc.pdf"],
    progress_callback=callback_fn
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `urls` | List[str] | Yes | - | List of URLs pointing to documents |
| `mode` | str | No | "DEFAULT" | Processing mode: "DEFAULT" or "ADVANCED" |
| `max_poll_time` | float | No | - | Maximum time to wait for completion |
| `poll_interval` | float | No | - | Time between status checks |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `show_progress` | bool | No | False | Whether to show a progress bar using tqdm |

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_s3_buckets()

List available S3 buckets

```python
buckets = await client.list_s3_buckets()
```

**Parameters:** (None)

**Returns:** `BucketListResponse` - Collection of S3 Buckets

#### list_s3_folders(bucket_name)

List folders in an S3 bucket

```python
folders = await client.list_s3_folders("MY_BUCKET")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `bucket_name` | str | Yes | - | Name of the S3 bucket |

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_s3_folder(bucket_name, folder_path, **options)

Parse files from an S3 folder

```python
documents = await client.parse_s3_folder("MY_BUCKET", "MY_FOLDER")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `bucket_name` | str | Yes | - | Name of the S3 bucket |
| `folder_path` | str | Yes | - | Path to the folder within the bucket |
| `mode` | str | No | "DEFAULT" | Processing mode: "DEFAULT" or "ADVANCED" |
| `max_poll_time` | float | No | - | Maximum time to wait for completion |
| `poll_interval` | float | No | - | Time between status checks |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `show_progress` | bool | No | False | Whether to show a progress bar using tqdm |

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_box_folders()

List available Box folders

```python
folders = await client.list_box_folders()
```

**Parameters:** (None)

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_box_folder(box_folder_id, **options)

Parse files from a Box folder

```python
documents = await client.parse_box_folder("box_folder_id")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `box_folder_id` | str | Yes | - | Box folder ID to process |
| `mode` | str | No | "DEFAULT" | Processing mode: "DEFAULT" or "ADVANCED" |
| `max_poll_time` | float | No | - | Maximum time to wait for completion |
| `poll_interval` | float | No | - | Time between status checks |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `show_progress` | bool | No | False | Whether to show a progress bar using tqdm |

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_dropbox_folders()

List available Dropbox folders

```python
folders = await client.list_dropbox_folders()
```

**Parameters:** (None)

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_dropbox_folder(folder_path, **options)

Parse files from a Dropbox folder

```python
documents = await client.parse_dropbox_folder("DROPBOX_FOLDER")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_path` | str | Yes | - | Dropbox folder path to process |
| `mode` | str | No | "DEFAULT" | Processing mode: "DEFAULT" or "ADVANCED" |
| `max_poll_time` | float | No | - | Maximum time to wait for completion |
| `poll_interval` | float | No | - | Time between status checks |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `show_progress` | bool | No | False | Whether to show a progress bar using tqdm |

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_sharepoint_sites()

List available SharePoint sites

```python
sites = await client.list_sharepoint_sites()
```

**Parameters:** (None)

**Returns:** `SiteListResponse` - Collection of Sharepoint Sites

#### list_sharepoint_drives(site_id)

List drives in a SharePoint site

```python
drives = await client.list_sharepoint_drives("MY_SITE")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `site_id` | str | Yes | - | SharePoint Site ID |

**Returns:** `DriveListResponse` - Collection of Sharepoint Drives

#### list_sharepoint_folders(drive_id)

List folders in a drive

```python
folders = await client.list_sharepoint_folders("MY_DRIVE")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `drive_id` | str | Yes | - | SharePoint Drive ID |

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_sharepoint_folder(drive_id, folder_id, **options)

Parse files from a SharePoint folder

```python
documents = await client.parse_sharepoint_folder("MY_DRIVE", "MY_FOLDER")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `drive_id` | str | Yes | - | Drive ID within the site |
| `folder_id` | str | Yes | - | Microsoft folder ID to process |
| `mode` | str | No | "DEFAULT" | Processing mode: "DEFAULT" or "ADVANCED" |
| `max_poll_time` | float | No | - | Maximum time to wait for completion |
| `poll_interval` | float | No | - | Time between status checks |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `show_progress` | bool | No | False | Whether to show a progress bar using tqdm |

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_salesforce_folders()

List available Salesforce folders

```python
folders = await client.list_salesforce_folders()
```

**Parameters:** (None)

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_salesforce_folder(folder_name, **options)

Parse files from a Salesforce folder

```python
documents = await client.parse_salesforce_folder("MY_FOLDER")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `folder_name` | str | Yes | - | Name of the folder for organization |
| `mode` | str | No | "DEFAULT" | Processing mode: "DEFAULT" or "ADVANCED" |
| `max_poll_time` | float | No | - | Maximum time to wait for completion |
| `poll_interval` | float | No | - | Time between status checks |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `show_progress` | bool | No | False | Whether to show a progress bar using tqdm |

**Returns:** `DocumentBatch` - Collection of parsed documents

#### parse_sendme_files(ticket)

Parse files from Sendme

```python
documents = await client.parse_sendme_files("TICKET_ID")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ticket` | str | Yes | - | Sendme ticket ID |
| `mode` | str | No | "DEFAULT" | Processing mode: "DEFAULT" or "ADVANCED" |
| `max_poll_time` | float | No | - | Maximum time to wait for completion |
| `poll_interval` | float | No | - | Time between status checks |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `show_progress` | bool | No | False | Whether to show a progress bar using tqdm |

**Returns:** `DocumentBatch` - Collection of parsed documents

---

## Lexa

Synchronous client for document processing (legacy/compatibility).

### Constructor

```python
Lexa(api_key: str, **options)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | str | Yes | - | Your Cerevox API key from [cerevox.ai/lexa](https://cerevox.ai/lexa) |
| `base_url` | str | No | (Cerevox Base URL) | Base URL of the Cerevox API |
| `max_concurrent` | int | No | 10 | Maximum number of concurrent processing jobs |
| `max_poll_time` | float | No | 600.0 | Maximum time to poll for job completion |
| `max_retries` | int | No | 3 | Maximum retry attempts for failed requests |
| `timeout` | float | No | 30.0 | Request timeout in seconds |

### Methods

#### parse(files, **options)

Parse documents from local files or file paths (synchronous).

**Parameters:** Same as AsyncLexa.parse()

**Returns:** `DocumentBatch` - Collection of parsed documents

#### parse_urls(urls, **options)

Parse documents from URLs (synchronous).

**Parameters:** Same as AsyncLexa.parse_urls()

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_s3_buckets()

List available S3 buckets (synchronous)

**Parameters:** (None)

**Returns:** `BucketListResponse` - Collection of S3 Buckets

#### list_s3_folders(bucket_name)

List folders in an S3 bucket (synchronous)

**Parameters:** Same as AsyncLexa.list_s3_folders()

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_s3_folder(bucket_name, folder_path, **options)

Parse files from an S3 folder (synchronous)

**Parameters:** Same as AsyncLexa.parse_s3_folder()

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_box_folders()

List available Box folders (synchronous)

**Parameters:** (None)

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_box_folder(box_folder_id, **options)

Parse files from a Box folder (synchronous)

**Parameters:** Same as AsyncLexa.parse_box_folder()

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_dropbox_folders()

List available Dropbox folders (synchronous)

**Parameters:** (None)

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_dropbox_folder(folder_path, **options)

Parse files from a Dropbox folder (synchronous)

**Parameters:** Same as AsyncLexa.parse_dropbox_folder()

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_sharepoint_sites()

List available SharePoint sites (synchronous)

**Parameters:** (None)

**Returns:** `SiteListResponse` - Collection of Sharepoint Sites

#### list_sharepoint_drives(site_id)

List drives in a SharePoint site (synchronous)

**Parameters:** Same as AsyncLexa.list_sharepoint_drives()

**Returns:** `DriveListResponse` - Collection of Sharepoint Drives

#### list_sharepoint_folders(drive_id)

List folders in a drive (synchronous)

**Parameters:** Same as AsyncLexa.list_sharepoint_folders()

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_sharepoint_folder(drive_id, folder_id, **options)

Parse files from a SharePoint folder (synchronous)

**Parameters:** Same as AsyncLexa.parse_sharepoint_folder()

**Returns:** `DocumentBatch` - Collection of parsed documents

#### list_salesforce_folders()

List available Salesforce folders (synchronous)

**Parameters:** (None)

**Returns:** `FolderListResponse` - Collection of Folders

#### parse_salesforce_folder(folder_name, **options)

Parse files from a Salesforce folder (synchronous)

**Parameters:** Same as AsyncLexa.parse_salesforce_folder()

**Returns:** `DocumentBatch` - Collection of parsed documents

#### parse_sendme_files(ticket)

Parse files from Sendme (synchronous)

**Parameters:** Same as AsyncLexa.parse_sendme_files()

**Returns:** `DocumentBatch` - Collection of parsed documents