import requests
from schemas.mediastore import IdentifierTypeSchema, S3ConfigSchemaCreate, S3ConfigSchemaSansKeys, StoreConfigSchema, StoreConfigSchemaCreate
from typing import Dict, List, Optional
from utils.custom_exception import BadRequestException, ClientError, NonRetryableError, RetryableError

class ApiResponse:
    def __init__(self, status_code: int, response: Optional[Dict] = None, exception: Optional[Exception] = None):
        self.status_code = status_code
        if response:
            self.response = response
        if exception:
            self.exception = exception

    def __str__(self) -> str:
        attrs = [f"Status code: {self.status_code}"]
        if self.response:
            attrs.append(f"Response: {self.response}")
        elif self.exception:
            attrs.append(f"Error: {self.error_message}")
        return ", ".join(attrs)

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

    def create_media(self, create_params: dict):
        """
        method to search for media using tags.
        """
        search_url = f"{self.base_url}/api/media/create"
        
        if not self.token:
            raise Exception("No bearer token found. Please login first.")
        
        
        response = requests.post(search_url, headers=self.headers, params=create_params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to search media. Status code: {response.status_code} Response: {response.content}")

    def search_media(self, search_params: dict):
        """
        method to search for media using tags.
        """
        search_url = f"{self.base_url}/api/media/search"
        
        if not self.token:
            raise Exception("No bearer token found. Please login first.")
        
        response = requests.post(search_url, headers=self.headers, params=search_params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to search media. Status code: {response.status_code} Response: {response.content}")

    def list_media(self):
        """
        method to list all media.
        """
        search_url = f"{self.base_url}/api/media/dump"
        
        if not self.token:
            raise Exception("No bearer token found. Please login first.")
        
        response = requests.get(search_url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list media. Status code: {response.status_code}  Response: {response.content}")

    def make_request(self, url: str, method: str, params: Optional[Dict]=None):
        """
        Generic method to make http requests and return response data
        """
        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        # Set headers and params
        request_kwargs = {'headers': self.headers}
        if params:
            request_kwargs['json'] = params.model_dump()
        # Set custom kwargs, e.g. as_schema (todo)
        # request_kwargs.update(kwargs)

        if method == 'get':
            response = requests.get(url, **request_kwargs)
        elif method == 'post':
            response = requests.post(url, **request_kwargs)
        elif method == 'put':
            response = requests.put(url, **request_kwargs)
        elif method == 'delete':
            response = requests.delete(url, **request_kwargs)
        else:
            return ApiResponse(
                status_code = 405,
                exception = BadRequestException(f'Method not supported: {method}')
            )

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
        elif sc == 422:
            return ApiResponse(
                status_code = sc,
                exception = BadRequestException(f"Invalid request: {params}. Response: {response.content}")
            )
        else:
            return ApiResponse(
                status_code = sc,
                exception = Exception(f"Failed to execute {method} request. Response: {response.content}")
            )

    def list_stores(self) -> List[StoreConfigSchema]:
        """
        List all stores.
        """
        url = f"{self.base_url}/api/stores"
        return self.make_request(url, method='get')

    def get_store(self, store_id) -> StoreConfigSchema:
        """
        Get store by id.
        """
        url = f"{self.base_url}/api/store/{store_id}"
        return self.make_request(url, method='get')

    def create_store(self, create_params: StoreConfigSchemaCreate) -> StoreConfigSchema:
        """
        Create a store.
        """
        url = f"{self.base_url}/api/store"
        return self.make_request(url, method='post', params=create_params)

    def delete_store(self, store_id):
        """
        Delete a store.
        """
        url = f"{self.base_url}/api/store/{store_id}"
        return self.make_request(url, method='delete')

    def list_s3cfgs(self) -> List[S3ConfigSchemaSansKeys]:
        """
        List all s3cfgs.
        """
        url = f"{self.base_url}/api/s3cfgs"
        return self.make_request(url, method='get')

    def get_s3cfg(self, s3cfg_id) -> S3ConfigSchemaSansKeys:
        """
        Get s3cfg by id.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"
        return self.make_request(url, method='get')

    def create_s3cfg(self, create_params: S3ConfigSchemaCreate) -> S3ConfigSchemaSansKeys:
        """
        Create a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg"
        return self.make_request(url, method='post', params=create_params)

    def update_s3cfg(self, s3cfg_id, update_params: S3ConfigSchemaCreate):
        """
        Update a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"
        return self.make_request(url, method='put', params=update_params)

    def delete_s3cfg(self, s3cfg_id):
        """
        Delete a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"
        return self.make_request(url, method='delete')

    def list_identifiers(self) -> List[IdentifierTypeSchema]:
        """
        List all identifiers.
        """
        url = f"{self.base_url}/api/identifier/list"
        return self.make_request(url, method='get')

    def get_identifier(self, identifier_name) -> IdentifierTypeSchema:
        """
        Get identifier by name.
        """
        url = f"{self.base_url}/api/identifier/{identifier_name}"
        return self.make_request(url, method='get')

    def create_identifier(self, create_params: IdentifierTypeSchema) -> IdentifierTypeSchema:
        """
        Create an identifier.
        """
        url = f"{self.base_url}/api/identifier"
        return self.make_request(url, method='post', params=create_params)

    def update_identifier(self, update_params: IdentifierTypeSchema):
        """
        Update an identifier.
        """
        url = f"{self.base_url}/api/identifier"
        return self.make_request(url, method='put', params=update_params)

    def delete_identifier(self, identifier_name: str):
        """
        Delete an identifier.
        """
        url = f"{self.base_url}/api/identifier/{identifier_name}"
        return self.make_request(url, method='delete')

    def upload_media(self, upload_params: dict):
        """
        upload a media object.
        """
        url = f"{self.base_url}/api/upload"
        return self.make_request(url, method='post', params=upload_params)

    def get_download_media_urls(self, download_pids: list[str]):
        """
        Get download urls for multiple media objects.
        """
        url = f"{self.base_url}/api/download/urls"
        return self.make_request(url, method='post', params=download_pids)

    def get_download_media_url(self, media_pid):
        """
        Get a download url for a media object.
        """
        url = f"{self.base_url}/api/download/url/{media_pid}"
        return self.make_request(url, method='get')

    def get_download_media(self, media_pid):
        """
        Directly download a media object.
        """
        url = f"{self.base_url}/api/download/{media_pid}"
        return self.make_request(url, method='get')