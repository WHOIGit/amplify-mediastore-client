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

