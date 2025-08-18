# Lexa API Reference

## Table of Contents

- [AsyncLexa](#asynclexa)
  - [Constructor](#constructor)
  - [Methods](#methods)
    - [parse(files, **options)](#parsefiles-options)
    - [parse_urls(urls, **options)](#parse_urlsurls-options)
- [Lexa](#lexa)
  - [Constructor](#constructor-1)
  - [Methods](#methods-1)
    - [parse(files, **options)](#parsefiles-options-1)
    - [parse_urls(urls, **options)](#parse_urlsurls-options-1)

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
    mode="STANDARD"
)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `files` | List[str] | Yes | - | List of file paths to parse |
| `progress_callback` | Callable | No | None | Function to track parsing progress |
| `mode` | str | No | "STANDARD" | Processing mode: "STANDARD" or "ADVANCED" |

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
| `progress_callback` | Callable | No | None | Function to track parsing progress |

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
| `max_concurrent` | int | No | 10 | Maximum number of concurrent processing jobs |
| `timeout` | float | No | 60.0 | Request timeout in seconds |
| `max_retries` | int | No | 3 | Maximum retry attempts for failed requests |

### Methods

#### parse(files, **options)

Parse documents from local files or file paths (synchronous).

**Parameters:** Same as AsyncLexa.parse()

**Returns:** `DocumentBatch` - Collection of parsed documents

#### parse_urls(urls, **options)

Parse documents from URLs (synchronous).

**Parameters:** Same as AsyncLexa.parse_urls()

**Returns:** `DocumentBatch` - Collection of parsed documents
