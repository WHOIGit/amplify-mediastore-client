# Usage Example
from apiclient import ApiClient

def test_media_create():
    # Initialize the client with your API base URL and credentials
    client = ApiClient(base_url="https://amplify-mediastore.whoi.edu", username="sa-mediastore", password="welcometo_homeofthe_")
    
    # Use the client to call APIs
    print(client.hello())

    search_params = {
        "tags": [
            "s3"
        ]
        }
    try:
        search_results = client.search_media(search_params)
        print(search_results)

    except Exception as e:
        print(str(e))

    try:
        list_results = client.list_media()
        print(list_results)
        
    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    test_media_create()
