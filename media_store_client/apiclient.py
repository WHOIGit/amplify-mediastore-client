from pathlib import Path
from pydantic import BaseModel, ValidationError
from schemas.mediastore import BulkUpdateResponseSchema, IdentifierTypeSchema, MediaSchema, MediaSchemaCreate, MediaSchemaUpdateIdentifiers, MediaSchemaUpdateMetadata, MediaSchemaUpdate, \
    MediaSchemaUpdateStorekey, MediaSchemaUpdateTags, MediaSearchSchema, S3ConfigSchemaCreate, S3ConfigSchemaSansKeys, StoreConfigSchema, StoreConfigSchemaCreate, UploadSchemaInput
from typing import Dict, List, Optional, Type, Union
from .utils.api_response import ApiResponse
from .utils.custom_exception import BadRequestException, ClientError, LocalError, ServerError
import base64
import requests

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

    def make_request(self, url: str, method: str, params: Optional[Dict]=None) -> ApiResponse:
        """
        Generic method to make http requests and return response data
        """
        if not self.token:
            raise LocalError(
                ApiResponse(
                    status_code = 401,
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
                    error_message = response.content
                )
            )
        elif 500 <= sc < 600:
            raise ServerError(
                response = ApiResponse(
                    status_code = sc,
                    error_message = response.content
                )
            )
        else:
            raise Exception(
                ApiResponse(
                    status_code = sc,
                    error_message = response.content
                )
            )

    def validate_schema(self, schema_class: Type[BaseModel], schema_params: Dict) -> Dict:
        """
        Generic method to validate data against its corresponding schema
        """
        try:
            schema = schema_class(**schema_params)
            return schema.model_dump()
        except ValidationError as e:
            raise ClientError(
                response = ApiResponse(
                    status_code = 400,
                    error_message = f'Schema validation failed for {schema_class.__name__}'
                )
            )

    def list_media(self) -> ApiResponse:
        """
        method to list all media.
        """
        url = f"{self.base_url}/api/media/dump"
        return self.make_request(url, method='get')

    def get_single_media(self, pid: str) -> ApiResponse:
        """
        Get media by id.
        """
        url = f"{self.base_url}/api/media/{pid}"
        return self.make_request(url, method='get')

    def create_single_media(self, pid: str, pid_type: str, store_config: Dict, identifiers: Optional[Dict] = None, metadata: Optional[Dict] = None, tags: Optional[List[str]] = None) -> ApiResponse:
        """
        method to create single media.
        """
        media_params = {
            'pid': pid,
            'pid_type': pid_type,
            'store_config': StoreConfigSchemaCreate(**store_config)
        }
        if identifiers:
            media_params['identifiers'] = identifiers
        if metadata:
            media_params['metadata'] = metadata
        if tags:
            media_params['tags'] = tags

        media = self.validate_schema(MediaSchemaCreate, media_params)
        url = f"{self.base_url}/api/media"
        return self.make_request(url, method='post', params=media)

    def update_single_media(self, pid: str, new_pid: Optional[str] = None, pid_type: Optional[str] = None, store_config: Optional[Union[Dict, int]] = None) -> ApiResponse:
        """
        method to update single media.
        """
        media_schema_update_params = {
            'pid': pid
        }
        if new_pid:
            media_schema_update_params['new_pid'] = new_pid
        if pid_type:
            media_schema_update_params['pid_type'] = pid_type
        if store_config:
            media_schema_update_params['store_config'] = store_config

        media = self.validate_schema(MediaSchemaUpdate, media_schema_update_params)
        url = f"{self.base_url}/api/media/{pid}"
        return self.make_request(url, method='patch', params=media)

    def delete_single_media(self, pid: str) -> ApiResponse:
        """
        Delete media by id.
        """
        url = f"{self.base_url}/api/media/{pid}"
        return self.make_request(url, method='delete')

    def list_stores(self) -> ApiResponse:
        """
        List all stores.
        """
        url = f"{self.base_url}/api/stores"
        return self.make_request(url, method='get')

    def get_store(self, store_id: int) -> ApiResponse:
        """
        Get store by id.
        """
        url = f"{self.base_url}/api/store/{store_id}"
        return self.make_request(url, method='get')

    def create_store(self, type: str, bucket: str, s3_url: Optional[str] = None) -> ApiResponse:
        """
        Create a store.
        """
        store_params = {
            'type': type,
            'bucket': bucket
        }
        if s3_url:
            store_params['s3_url'] = s3_url

        store = self.validate_schema(StoreConfigSchemaCreate, store_params)
        url = f"{self.base_url}/api/store"
        return self.make_request(url, method='post', params=store)

    def delete_store(self, store_id: int) -> ApiResponse:
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

    def get_s3cfg(self, s3cfg_id: int) -> ApiResponse:
        """
        Get s3cfg by id.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"
        return self.make_request(url, method='get')

    def create_s3cfg(self, url: str, access_key: str, secret_key: str) -> ApiResponse:
        """
        Create a s3cfg.
        """
        s3_config_params = {
            'url': url,
            'access_key': access_key,
            'secret_key': secret_key
        }

        s3_config = self.validate_schema(S3ConfigSchemaCreate, s3_config_params)
        url = f"{self.base_url}/api/s3cfg"
        return self.make_request(url, method='post', params=s3_config)

    def update_s3cfg(self, s3cfg_id: int, url: str, access_key: str, secret_key: str) -> ApiResponse:
        """
        Update a s3cfg.
        """
        s3_config_params = {
            'url': url,
            'access_key': access_key,
            'secret_key': secret_key
        }

        s3_config = self.validate_schema(S3ConfigSchemaCreate, s3_config_params)
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"
        return self.make_request(url, method='put', params=s3_config)

    def delete_s3cfg(self, s3cfg_id: int) -> ApiResponse:
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

    def get_identifier(self, identifier_name: str) -> ApiResponse:
        """
        Get identifier by name.
        """
        url = f"{self.base_url}/api/identifier/{identifier_name}"
        return self.make_request(url, method='get')

    def _create_update_identifier(self, method: str, name: str, pattern: Optional[str] = None):
        identifier_params = {
            'name': name
        }
        if pattern:
            identifier_params['pattern'] = pattern

        identifier = self.validate_schema(IdentifierTypeSchema, identifier_params)
        url = f"{self.base_url}/api/identifier"
        return self.make_request(url, method=method, params=identifier)

    def create_identifier(self, name: str, pattern: Optional[str] = None) -> ApiResponse:
        """
        Create an identifier.
        """
        return self._create_update_identifier(method='post', name=name, pattern=pattern)

    def update_identifier(self, name: str, pattern: Optional[str] = None) -> ApiResponse:
        """
        Update an identifier.
        """
        return self._create_update_identifier(method='put', name=name, pattern=pattern)

    def delete_identifier(self, identifier_name: str) -> ApiResponse:
        """
        Delete an identifier.
        """
        url = f"{self.base_url}/api/identifier/{identifier_name}"
        return self.make_request(url, method='delete')

    def upload_media(self, filepath: Union[str,Path], pid: str, pid_type: str, store_config: Dict, identifiers: Optional[Dict] = None, metadata: Optional[Dict] = None, tags: Optional[List[str]] = None) -> ApiResponse:
        """
        upload a media object.
        """
        mediadata_params = {
            'pid': pid,
            'pid_type': pid_type,
            'store_config': StoreConfigSchemaCreate(**store_config)
        }
        if identifiers:
            mediadata_params['identifiers'] = identifiers
        if metadata:
            mediadata_params['metadata'] = metadata
        if tags:
            mediadata_params['tags'] = tags
        with open(filepath, 'rb') as file:
            file_data = base64.b64encode(file.read())

        upload_schema_input = UploadSchemaInput(
            mediadata = MediaSchemaCreate(**mediadata_params),
            base64 = file_data
        )
        url = f"{self.base_url}/api/upload"
        return self.make_request(url, method='post', params=upload_schema_input.model_dump())

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

    def create_bulk_media(self, media_list: List[Dict]) -> ApiResponse:
        """
        Create a list of media objects
        """
        media_schemas = []
        for media_item in media_list:
            mediadata_params = {
                'pid': media_item['pid'],
                'pid_type': media_item['pid_type'],
                'store_config': StoreConfigSchemaCreate(**media_item['store_config'])
            }

            if 'identifiers' in media_item:
                mediadata_params['identifiers'] = media_item['identifiers']
            if 'metadata' in media_item:
                mediadata_params['metadata'] = media_item['metadata']
            if 'tags' in media_item:
                mediadata_params['tags'] = media_item['tags']

            media_schemas.append(MediaSchemaCreate(**mediadata_params))

        url = f'{self.base_url}/api/media/create'
        media_schema_list = [media_schema.model_dump() for media_schema in media_schemas]
        return self.make_request(url, method='post', params=media_schema_list)

    def get_bulk_media(self, pid_list: List[str]) -> ApiResponse:
        """
        Find media objects by pid
        """
        url = f'{self.base_url}/api/media/read'
        return self.make_request(url, method='post', params=pid_list)

    def update_bulk_media(self, pids: List[str], medias: List[Dict]) -> ApiResponse:
        """
        method to update bulk media.
        """
        media_update_schemas = []
        for media in medias:
            media_schema_update = MediaSchemaUpdate(**media)
            media_update_schemas.append(media_schema_update)
        media_update_list = [media_update_schema.model_dump() for media_update_schema in media_update_schemas]

        update_bulk_media_params = {
            'pids': pids,
            'medias': media_update_list
        }
        url = f"{self.base_url}/api/media/update"
        return self.make_request(url, method='patch', params=update_bulk_media_params)

    def search_bulk_media(self, search_tags: List[str]) -> ApiResponse:
        """
        Find media objects by tags and other vectors
        """
        media_search_schema = MediaSearchSchema(
            tags = search_tags
        )
        url = f'{self.base_url}/api/media/search'
        return self.make_request(url, method='post', params=media_search_schema.model_dump())

    def delete_bulk_media(self, pid_list: List[str]) -> ApiResponse:
        """
        Delete media objects by pid
        """
        url = f'{self.base_url}/api/media/delete'
        return self.make_request(url, method='post', params=pid_list)

    def _patch_update_media_tags(self, tags_list: List[Dict], method: str) -> ApiResponse:
        media_tags_schemas = []
        for media_tag in tags_list:
            media_tags_schemas.append(MediaSchemaUpdateTags(
                pid = media_tag['pid'],
                tags = media_tag['tags']
            ))

        url = f'{self.base_url}/api/media/update/tags'
        media_tags_list = [media_tags_schema.model_dump() for media_tags_schema in media_tags_schemas]
        return self.make_request(url, method=method, params=media_tags_list)

    def patch_media_tags(self, tags_list: List[Dict]) -> ApiResponse:
        """
        Partially update tags for media objects
        """
        return self._patch_update_media_tags(tags_list, method='patch')

    def update_media_tags(self, tags_list: List[Dict]) -> ApiResponse:
        """
        Update tags for media objects
        """
        return self._patch_update_media_tags(tags_list, method='put')

    def update_media_storekeys(self, storekeys_list: List[Dict]) -> ApiResponse:
        """
        Update storekeys for media objects
        """
        media_storekeys_schemas = []
        for media_storekey in storekeys_list:
            media_storekeys_schemas.append(MediaSchemaUpdateStorekey(
                pid = media_storekey['pid'],
                store_key = media_storekey['store_key']
            ))

        url = f'{self.base_url}/api/media/update/storekeys'
        media_storekeys_list = [media_storekeys_schema.model_dump() for media_storekeys_schema in media_storekeys_schemas]
        return self.make_request(url, method='put', params=media_storekeys_list)

    def update_media_identifiers(self, identifiers_list: List[Dict]) -> ApiResponse:
        """
        Update identifiers for media objects
        """
        media_identifiers_schemas = []
        for media_identifier in identifiers_list:
            media_identifiers_schemas.append(MediaSchemaUpdateIdentifiers(
                pid = media_identifier['pid'],
                identifiers = media_identifier['identifiers']
            ))

        url = f'{self.base_url}/api/media/update/identifiers'
        media_identifiers_list = [media_identifiers_schema.model_dump() for media_identifiers_schema in media_identifiers_schemas]
        return self.make_request(url, method='put', params=media_identifiers_list)

    def _delete_patch_update_metadata(self, metadata_list: List[Dict], method: str) -> ApiResponse:
        media_metadata_schemas = []
        for metadata_item in metadata_list:
            media_metadata_params = {
                'pid': metadata_item['pid']
            }
            if 'keys' in metadata_item:
                media_metadata_params['keys'] = metadata_item['keys']
            if 'data' in metadata_item:
                media_metadata_params['data'] = metadata_item['data']
            media_metadata_schemas.append(MediaSchemaUpdateMetadata(**media_metadata_params))

        url = f'{self.base_url}/api/media/update/metadata'
        media_metadata_list = [media_metadata_schema.model_dump() for media_metadata_schema in media_metadata_schemas]
        return self.make_request(url, method=method, params = media_metadata_list)

    def update_media_metadata(self, metadata_list: List[Dict]) -> ApiResponse:
        """
        Update metadata for media objects
        """
        return self._delete_patch_update_metadata(metadata_list, method='put')

    def patch_media_metadata(self, metadata_list: List[Dict]) -> ApiResponse:
        """
        Partially update metadata for media objects
        """
        return self._delete_patch_update_metadata(metadata_list, method='patch')

    def delete_media_metadata(self, metadata_list: List[Dict]) -> ApiResponse:
        """
        Delete metadata for media objects
        """
        return self._delete_patch_update_metadata(metadata_list, method='delete')
