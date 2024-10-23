import requests
from utils.custom_exception import BadRequestException, ClientError, NonRetryableError, RetryableError

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

    def list_stores(self):
        """
        List all stores.
        """
        url = f"{self.base_url}/api/stores"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list stores. Status code: {response.status_code}  Response: {response.content}")

    def get_store(self, store_id):
        """
        Get store by id.
        """
        url = f"{self.base_url}/api/store/{store_id}"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get store (id {store_id}). Status code: {response.status_code}  Response: {response.content}")

    def create_store(self, create_params: dict):
        """
        Create a store.
        """
        url = f"{self.base_url}/api/store"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.post(url, headers=self.headers, json=create_params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            raise BadRequestException(f"Invalid request: {create_params}. Status code: {response.status_code}  Response: {response.content}")
        else:
            raise Exception(f"Failed to create store. Status code: {response.status_code}  Response: {response.content}")

    def delete_store(self, store_id):
        """
        Delete a store.
        """
        url = f"{self.base_url}/api/store/{store_id}"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.delete(url, headers=self.headers)

        if response.status_code == 204:
            return
        else:
            raise Exception(f"Failed to delete store. Status code: {response.status_code}  Response: {response.content}")

    def list_s3cfgs(self):
        """
        List all s3cfgs.
        """
        url = f"{self.base_url}/api/s3cfgs"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list s3cfgs. Status code: {response.status_code}  Response: {response.content}")

    def get_s3cfg(self, s3cfg_id):
        """
        Get s3cfg by id.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get s3cfg (id {s3cfg_id}). Status code: {response.status_code}  Response: {response.content}")

    def create_s3cfg(self, create_params: dict):
        """
        Create a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.post(url, headers=self.headers, json=create_params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            raise BadRequestException(f"Invalid request: {create_params}. Status code: {response.status_code}  Response: {response.content}")
        else:
            raise Exception(f"Failed to create s3cfg. Status code: {response.status_code}  Response: {response.content}")

    def update_s3cfg(self, s3cfg_id, update_params: dict):
        """
        Update a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.put(url, headers=self.headers, json=update_params)

        if response.status_code == 204:
            return
        elif response.status_code == 422:
            raise BadRequestException(f"Invalid request: {update_params}. Status code: {response.status_code}  Response: {response.content}")
        else:
            raise Exception(f"Failed to update s3cfg. Status code: {response.status_code}  Response: {response.content}")

    def delete_s3cfg(self, s3cfg_id):
        """
        Delete a s3cfg.
        """
        url = f"{self.base_url}/api/s3cfg/{s3cfg_id}"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.delete(url, headers=self.headers)

        if response.status_code == 204:
            return
        else:
            raise Exception(f"Failed to delete s3cfg. Status code: {response.status_code}  Response: {response.content}")

    def list_identifiers(self):
        """
        List all identifiers.
        """
        url = f"{self.base_url}/api/identifier/list"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list identifiers. Status code: {response.status_code}  Response: {response.content}")

    def get_identifier(self, identifier_name):
        """
        Get identifier by name.
        """
        url = f"{self.base_url}/api/identifier/{identifier_name}"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get identifier (name {identifier_name}). Status code: {response.status_code}  Response: {response.content}")

    def create_identifier(self, create_params: dict):
        """
        Create an identifier.
        """
        url = f"{self.base_url}/api/identifier"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.post(url, headers=self.headers, json=create_params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            raise BadRequestException(f"Invalid request: {create_params}. Status code: {response.status_code}  Response: {response.content}")
        else:
            raise Exception(f"Failed to create identifier. Status code: {response.status_code}  Response: {response.content}")

    def update_identifier(self, update_params: dict):
        """
        Update an identifier.
        """
        url = f"{self.base_url}/api/identifier"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.put(url, headers=self.headers, json=update_params)

        if response.status_code == 204:
            return
        elif response.status_code == 422:
            raise BadRequestException(f"Invalid request: {update_params}. Status code: {response.status_code}  Response: {response.content}")
        else:
            raise Exception(f"Failed to update identifier. Status code: {response.status_code}  Response: {response.content}")

    def delete_identifier(self, delete_params: dict):
        """
        Delete an identifier.
        """
        url = f"{self.base_url}/api/identifier"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.delete(url, headers=self.headers, json=delete_params)

        if response.status_code == 204:
            return
        else:
            raise Exception(f"Failed to delete identifier. Status code: {response.status_code}  Response: {response.content}")

    def upload_media(self, upload_params: dict):
        """
        upload a media object.
        """
        url = f"{self.base_url}/api/upload"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.post(url, headers=self.headers, json=upload_params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            raise BadRequestException(f"Invalid request: {upload_params}. Status code: {response.status_code}  Response: {response.content}")
        else:
            raise Exception(f"Failed to create identifier. Status code: {response.status_code}  Response: {response.content}")

    def get_download_media_urls(self, download_pids: list[str]):
        """
        Get download urls for multiple media objects.
        """
        url = f"{self.base_url}/api/download/urls"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.post(url, headers=self.headers, json=download_pids)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            raise BadRequestException(f"Invalid request: {download_pids}. Status code: {response.status_code}  Response: {response.content}")
        else:
            raise Exception(f"Failed to create identifier. Status code: {response.status_code}  Response: {response.content}")

    def get_download_media_url(self, media_pid):
        """
        Get a download url for a media object.
        """
        url = f"{self.base_url}/api/download/url/{media_pid}"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get download url for media object (name {media_pid}). Status code: {response.status_code}  Response: {response.content}")

    def get_download_media(self, media_pid):
        """
        Directly download a media object.
        """
        url = f"{self.base_url}/api/download/{media_pid}"

        if not self.token:
            raise ClientError("No bearer token found. Please login first.")

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get media object (name {media_pid}). Status code: {response.status_code}  Response: {response.content}")

    # def make_request(self, url, method, params=None):
    #     if not self.token:
    #         raise ClientError("No bearer token found. Please login first.")

    #     if method == 'get':
    #         response = requests.get(url, headers=self.headers)
    #     elif method == 'post' or method == 'put':
    #         response = requests.post(url, headers=self.headers, json=params)
    #     elif method == 'delete':
    #         response = requests.delete(url, headers=self.headers)
    #     else:
    #         raise Exception(f'Method not supported: {method}')

    #     sc = response.status_code
    #     if sc == 200:
    #         return response.json()
    #     elif sc == 204:
    #         return
    #     elif sc == 422:
    #         raise BadRequestException(f"Invalid request: {params}. Status code: {sc}  Response: {response.content}")
    #     else:
    #         raise Exception(f"Failed to execute {method} request. Status code: {sc}, Response: {response.content}")

    #     # Example usage
    #     url = f"{self.base_url}/api/some_model/{model_id}"
    #     return self.make_request(url, 'get')