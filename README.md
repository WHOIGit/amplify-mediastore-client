# Media Store API Client

A Python client library for interacting with the AMPLIfy Media Store API, providing simple interfaces for managing media objects, stores, S3 configurations, and identifiers.

> **Note**: This client requires the [Media Store API Service](https://github.com/WHOIGit/amplify-mediastore.git) to be running.

## Installation

```bash
pip install media-store-client  # Package name may vary
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
media_object = MediaSchemaCreate(
    title="My Media",
    tags=["video", "presentation"]
)
response = client.create_media_single(media_object)

# List all media
all_media = client.list_media()

# Get media by ID
media = client.get_media_by_pid("media_pid_123")

# Delete media
client.delete_media_by_pid("media_pid_123")
```

### Bulk Operations

```python
# Create multiple media objects
media_list = [
    MediaSchemaCreate(title="Media 1", tags=["video"]),
    MediaSchemaCreate(title="Media 2", tags=["image"])
]
response = client.create_bulk_media(media_list)

# Update tags for multiple media objects
tags_update = [
    MediaSchemaUpdateTags(pid="media_1", tags=["updated", "tags"]),
    MediaSchemaUpdateTags(pid="media_2", tags=["new", "tags"])
]
client.update_media_tags(tags_update)
```

### Store Management

```python
# List all stores
stores = client.list_stores()

# Create a new store
store_config = StoreConfigSchemaCreate(
    name="my_store",
    config={"key": "value"}
)
response = client.create_store(store_config)
```

### S3 Configuration

```python
# Create S3 configuration
s3_config = S3ConfigSchemaCreate(
    bucket="my-bucket",
    region="us-west-2"
)
response = client.create_s3cfg(s3_config)

# List all S3 configurations
s3_configs = client.list_s3cfgs()
```

### File Operations

```python
# Upload media
upload_params = UploadSchemaInput(
    file_path="/path/to/file",
    media_type="video/mp4"
)
response = client.upload_media(upload_params)

# Get download URL
download_url = client.get_download_media_url("media_pid_123")
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

## License

[Add your license information here]