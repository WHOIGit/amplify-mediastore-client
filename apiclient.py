import requests
from schemas.mediastore import BulkUpdateResponseSchema, IdentifierTypeSchema, MediaSchema, MediaSchemaCreate, MediaSchemaUpdateIdentifiers, MediaSchemaUpdateMetadata, MediaSchemaUpdate, \
    MediaSchemaUpdateStorekey, MediaSchemaUpdateTags, MediaSearchSchema, S3ConfigSchemaCreate, S3ConfigSchemaSansKeys, StoreConfigSchema, StoreConfigSchemaCreate, UploadSchemaInput
from typing import Dict, List, Optional
from utils.api_response import ApiResponse
from utils.custom_exception import BadRequestException, ClientError, LocalError, ServerError

class ApiClient:
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the ApiClient with base URL and credentials.
        Automatically fetches and stores the bearer token upon initialization.
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.headers = None
        self.login()
        self.default_reties = 3

    def login(self):
        """
        Fetch the bearer token using the provided credentials.
        """
        login_url = f"{self.base_url}/api/login"
        login_data = {
            "username": self.username,
            "password": self.password
        }

        response = requests.post(login_url, json=login_data)

        if response.status_code == 200:
            self.token = response.json().get('token')
            if self.token:
                self.headers = {'Authorization': f'Bearer {self.token}'}
                print("Successfully retrieved token.")
            else:
                raise Exception("Token not found in response.")
        else:
            raise Exception(f"Failed to retrieve token. Status code: {response.status_code}")

    def hello(self):
        ping_url = f"{self.base_url}/api/hello"
        response = requests.get(ping_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to ping media store. Status code: {response.status_code}")

    def create_media(self, create_params: List[MediaSchemaCreate]) -> ApiResponse:
        """
        method to create media in bulk.
        """
        url = f"{self.base_url}/api/media/create"
        media_list = []
        for media_item in create_params:
            media_list.append(media_item.model_dump())
        return self.make_request(url, method='post', params=media_list)

    def list_media(self) -> ApiResponse:
        """
        method to list all media.
        """
        url = f"{self.base_url}/api/media/dump"
        return self.make_request(url, method='get')

    def create_media_single(self, create_params: MediaSchemaCreate) -> ApiResponse:
        """
        method to create single media.
        """
        url = f"{self.base_url}/api/media"
        return self.make_request(url, method='post', params=create_params.model_dump())

    def get_media_by_pid(self, pid) -> ApiResponse:
        """
        Get media by id.
        """
        url = f"{self.base_url}/api/media/{pid}"
        return self.make_request(url, method='get')

    def delete_media_by_pid(self, pid) -> ApiResponse:
        """
        Delete media by id.
        """
        url = f"{self.base_url}/api/media/{pid}"
        return self.make_request(url, method='delete')
    
    def update_single_media(self, pid, update_params: MediaSchemaUpdate) -> ApiResponse:
        """
        method to update single media.
        """
        url = f"{self.base_url}/api/media/{pid}"
        return self.make_request(url, method='patch', params=update_params.model_dump())

    def update_bulk_media(self, update_params) -> ApiResponse:
        """
        method to update bulk media.
        """
        url = f"{self.base_url}/api/media/update"
        return self.make_request(url, method='patch', params=update_params)
        
    def make_request(self, url: str, method: str, params: Optional[Dict]=None) -> ApiResponse:
        """
        Generic method to make http requests and return response data
        """
        if not self.token:
            raise LocalError(
                ApiResponse(
                    status_code = 401,
                    response = None,
                    error_message = 'No bearer token found. Please login first.'
                )
            )

        # Set headers and params
        request_kwargs = {
            'headers': self.headers
        }
        if params:
            request_kwargs['json'] = params

        # Make appropriate http request
        if method == 'get':
            response = requests.get(url, **request_kwargs)
        elif method == 'patch':
            response = requests.patch(url, **request_kwargs)
        elif method == 'post':
            response = requests.post(url, **request_kwargs)
        elif method == 'put':
            response = requests.put(url, **request_kwargs)
        elif method == 'patch':
            response = requests.patch(url, **request_kwargs)
        elif method == 'delete':
            response = requests.delete(url, **request_kwargs)
        else:
            raise LocalError(
                response = ApiResponse (
                    status_code = 405,
                    response = None,
                    error_message = f'Method not supported: {method}'
                )
            )

        # Return an ApiResponse with relevant status/response/error
        sc = response.status_code
        if sc == 200:
            return ApiResponse(
                status_code = sc,
                response = response.json()
            )
        elif sc == 204:
            return ApiResponse(
                status_code = sc
            )
        elif 400 <= sc < 500:
            raise ClientError(
                response = ApiResponse(
                    status_code = sc,
                    response = response.content,
                    error_message = response.content
                )
            )
        elif 500 <= sc < 600:
            raise ServerError(
                response = ApiResponse(
                    status_code = sc,
                    response = response.content,
                    error_message = response.content
                )
            )
        else:
            raise Exception(
                ApiResponse(
                    status_code = sc,
                    response = response.content,
                    error_message = response.content
                )
            )

    def list_stores(self) -> ApiResponse:
        """
        List all stores.
        """
        url = f"{self.base_url}/api/stores"
        return self.make_request(url, method='get')

    def get_store(self, store_id) -> ApiResponse:
        """
        Get store by id.
        """
        url = f"{self.base_url}/api/store/{store_id}"
        return self.make_request(url, method='get')

    def create_store(self, create_params: StoreConfigSchemaCreate) -> ApiResponse:
        """
        Create a store.
        """
        url = f"{self.base_url}/api/store"
        return self.make_request(url, method='post', params=create_params.model_dump())

    def delete_store(self, store_id) -> ApiResponse:
        """
        Delete a store.
        """
        url = f"{self.base_url}/api/store/{store_id}"
        return self.make_request(url, method='delete')

    def list_s3cfgs(self) -> ApiResponse:
        """
        List all s3cfgs.
        """
        url = f"{self.base_url}/api/s3cfgs"
        return self.make_request(url, method='get')

    def get_s3cfg(self, s3cfg_id) -> ApiResponse:
        """
        Get s3cfg by id.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"
        return self.make_request(url, method='get')

    def create_s3cfg(self, create_params: S3ConfigSchemaCreate) -> ApiResponse:
        """
        Create a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg"
        return self.make_request(url, method='post', params=create_params.model_dump())

    def update_s3cfg(self, s3cfg_id, update_params: S3ConfigSchemaCreate) -> ApiResponse:
        """
        Update a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"
        return self.make_request(url, method='put', params=update_params.model_dump())

    def delete_s3cfg(self, s3cfg_id) -> ApiResponse:
        """
        Delete a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"
        return self.make_request(url, method='delete')

    def list_identifiers(self) -> ApiResponse:
        """
        List all identifiers.
        """
        url = f"{self.base_url}/api/identifier/list"
        return self.make_request(url, method='get')

    def get_identifier(self, identifier_name) -> ApiResponse:
        """
        Get identifier by name.
        """
        url = f"{self.base_url}/api/identifier/{identifier_name}"
        return self.make_request(url, method='get')

    def create_identifier(self, create_params: IdentifierTypeSchema) -> ApiResponse:
        """
        Create an identifier.
        """
        url = f"{self.base_url}/api/identifier"
        return self.make_request(url, method='post', params=create_params.model_dump())

    def update_identifier(self, update_params: IdentifierTypeSchema) -> ApiResponse:
        """
        Update an identifier.
        """
        url = f"{self.base_url}/api/identifier"
        return self.make_request(url, method='put', params=update_params.model_dump())

    def delete_identifier(self, identifier_name: str) -> ApiResponse:
        """
        Delete an identifier.
        """
        url = f"{self.base_url}/api/identifier/{identifier_name}"
        return self.make_request(url, method='delete')

    def upload_media(self, upload_params: UploadSchemaInput) -> ApiResponse:
        """
        upload a media object.
        """
        url = f"{self.base_url}/api/upload"
        return self.make_request(url, method='post', params=upload_params.model_dump())

    def get_download_media_urls(self, download_pids: List[str]) -> ApiResponse:
        """
        Get download urls for multiple media objects.
        """
        url = f"{self.base_url}/api/download/urls"
        return self.make_request(url, method='post', params=download_pids)

    def get_download_media_url(self, media_pid: str) -> ApiResponse:
        """
        Get a download url for a media object.
        """
        url = f"{self.base_url}/api/download/url/{media_pid}"
        return self.make_request(url, method='get')

    def get_download_media(self, media_pid: str) -> ApiResponse:
        """
        Directly download a media object.
        """
        url = f"{self.base_url}/api/download/{media_pid}"
        return self.make_request(url, method='get')

    def create_bulk_media(self, media_list: List[MediaSchemaCreate]) -> ApiResponse:
        """
        Create a list of media objects
        """
        url = f'{self.base_url}/api/media/create'
        media_list_dict = [media.model_dump() for media in media_list]
        return self.make_request(url, method='post', params=media_list_dict)

    def read_bulk_media(self, pid_list: List[str]) -> ApiResponse:
        """
        Find media objects by pid
        """
        url = f'{self.base_url}/api/media/read'
        return self.make_request(url, method='post', params=pid_list)

    def search_bulk_media(self, search_params: MediaSearchSchema) -> ApiResponse:
        """
        Find media objects by tags and other vectors
        """
        url = f'{self.base_url}/api/media/search'
        return self.make_request(url, method='post', params=search_params.model_dump())

    def delete_bulk_media(self, pid_list: List[str]) -> ApiResponse:
        """
        Delete media objects by pid
        """
        url = f'{self.base_url}/api/media/delete'
        return self.make_request(url, method='post', params=pid_list)

    def patch_media_tags(self, tags_list: List[MediaSchemaUpdateTags]) -> ApiResponse:
        """
        Partially update tags for media objects
        """
        url = f'{self.base_url}/api/media/update/tags'
        tags_list_dict = [tags.model_dump() for tags in tags_list]
        return self.make_request(url, method='patch', params=tags_list_dict)

    def update_media_tags(self, tags_list: List[MediaSchemaUpdateTags]) -> ApiResponse:
        """
        Update tags for media objects
        """
        url = f'{self.base_url}/api/media/update/tags'
        tags_list_dict = [tags.model_dump() for tags in tags_list]
        return self.make_request(url, method='put', params=tags_list_dict)

    def update_media_storekeys(self, storekeys_list: List[MediaSchemaUpdateStorekey]) -> ApiResponse:
        """
        Update storekeys for media objects
        """
        url = f'{self.base_url}/api/media/update/storekeys'
        storekeys_list_dict = [storekeys.model_dump() for storekeys in storekeys_list]
        return self.make_request(url, method='put', params=storekeys_list_dict)

    def update_media_identifiers(self, identifiers_list: List[MediaSchemaUpdateIdentifiers]) -> ApiResponse:
        """
        Update identifiers for media objects
        """
        url = f'{self.base_url}/api/media/update/identifiers'
        identifiers_list_dict = [identifiers.model_dump() for identifiers in identifiers_list]
        return self.make_request(url, method='put', params=identifiers_list_dict)

    def update_media_metadata(self, metadata_list: List[MediaSchemaUpdateMetadata]) -> ApiResponse:
        """
        Update metadata for media objects
        """
        url = f'{self.base_url}/api/media/update/metadata'
        metadata_list_dict = [metadata.model_dump() for metadata in metadata_list]
        return self.make_request(url, method='put', params=metadata_list_dict)

    def patch_media_metadata(self, metadata_list: List[MediaSchemaUpdateMetadata]) -> ApiResponse:
        """
        Partially update metadata for media objects
        """
        url = f'{self.base_url}/api/media/update/metadata'
        metadata_list_dict = [metadata.model_dump() for metadata in metadata_list]
        return self.make_request(url, method='patch', params=metadata_list_dict)

    def delete_media_metadata(self, metadata_list: List[MediaSchemaUpdateMetadata]) -> ApiResponse:
        """
        Delete metadata for media objects
        """
        url = f'{self.base_url}/api/media/update/metadata'
        metadata_list_dict = [metadata.model_dump() for metadata in metadata_list]
        return self.make_request(url, method='delete', params=metadata_list_dict)