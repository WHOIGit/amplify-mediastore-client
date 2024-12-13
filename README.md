# Media Store API Client

A Python client library for interacting with the AMPLIfy Media Store API, providing a simple interface for managing media objects, stores, and S3 configurations.

> **Note**: This client requires the [Media Store API Service](https://github.com/WHOIGit/amplify-mediastore.git) to be running.

## Installation

```bash
pip install media-store-client
```

## Quick Start

```python
from media_store_client import ApiClient

# Initialize the client
client = ApiClient(
    base_url="https://api.mediastore.example.com",
    username="your_username",
    password="your_password"
)

# Test connection
response = client.hello()
```

## Usage Examples

### Media Operations

```python
# Create a single media object
response = client.create_single_media(
    pid="media_123",
    pid_type="DEMO",
    store_config={"type": "DictStore", "bucket": "test_bucket"},
    (...)
    tags=["test"]
)

# List all media
all_media = client.list_media()

# Get media by ID
media = client.get_single_media("media_123")

# Delete media
client.delete_single_media("media_123")
```

### Bulk Operations

```python
# Create multiple media objects
media_list = [
    {
        "pid": "media_123",
        "pid_type": "DEMO",
        "store_config": {"type": "DictStore", "bucket": "test_bucket"},
    },
    (...)
]
response = client.create_bulk_media(media_list)

# Update tags for multiple media objects
tags_update = [
    {"pid": "media_123", "tags": ["new_tag1"]},
    (...)
]
client.update_media_tags(tags_update)
```

### Store Management

```python
# List all stores
stores = client.list_stores()

# Create a new store
response = client.create_store(
    type="BucketStore",
    bucket="test_bucket",
    s3_url="demo.example.com"
)
```

### S3 Configuration

```python
# Create S3 configuration
response = client.create_s3cfg(
    url="https://s3.example.com",
    access_key="access_key",
    secret_key="secret_key"
)

# List all S3 configurations
s3_configs = client.list_s3cfgs()
```

### File Operations

```python
# Upload media
response = client.upload_media(
    filepath="path/to/file.jpg",
    pid="media_123",
    pid_type="DEMO",
    store_config={"type": "DictStore", "bucket": "test_bucket"},
    metadata={"title": "Test Upload"}
)

# Get download URL
download_url = client.get_download_media_url("media_123")
```

## Error Handling

The client implements comprehensive error handling with specific exceptions:

- `ClientError`: For HTTP 4xx errors from the server
- `ServerError`: For HTTP 5xx errors from the server
- `LocalError`: For errors raised from the client-code
- `BadRequestException`: For unsupported methods

Example:

```python
try:
    response = client.get_media_by_pid("invalid_pid")
except ClientError as e:
    print(f"Client error: {e.response.error_message}")
except ServerError as e:
    print(f"Server error: {e.response.error_message}")
```

## Response Format

All API responses are wrapped in an `ApiResponse` object with the following structure:

```python
class ApiResponse:
    status_code: int
    response: Optional[Dict]
    error_message: Optional[str]
```

## Authentication

The client handles authentication automatically on initialization. If the token expires, you can manually refresh it:

```python
client.login()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
