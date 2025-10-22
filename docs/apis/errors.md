# Errors API Reference

## Table of Contents

- [Error Handling](#error-handling)
  - [Exception Classes](#exception-classes)
  - [Error Handling Example](#error-handling-example)

---

## Error Handling

### Exception Classes

```python
from cerevox import (
    LexaError,
    LexaAuthError,
    LexaJobFailedError,
    LexaTimeoutError
)
```

| Exception | Description |
|-----------|-------------|
| `LexaError` | Base exception for all Cerevox errors |
| `LexaAuthError` | Authentication-related errors |
| `LexaJobFailedError` | Document processing job failures |
| `LexaTimeoutError` | Request timeout errors |

### Error Handling Example

```python
try:
    documents = await client.parse(files)
except LexaAuthError as e:
    print(f"Authentication failed: {e.message}")
except LexaJobFailedError as e:
    print(f"Job failed: {e.message}")
except LexaTimeoutError as e:
    print(f"Timeout: {e.message} (status: {e.status_code})")
except LexaError as e:
    print(f"General error: {e.message}")
``` 