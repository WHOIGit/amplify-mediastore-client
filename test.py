from apiclient import ApiClient
from utils.custom_exception import BadRequestException

# Usage Example

client = ApiClient(base_url="https://amplify-mediastore.whoi.edu", username="sa-mediastore", password="welcometo_homeofthe_")

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


####################################
## Stores
####################################

def list_stores():
    stores = client.list_stores()
    print(f'All stores: {stores}')

def test_create_store():
    print('\nCreating store')
    print('================')
    # Create store
    create_params = {
        "type": "DictStore",
        "bucket": "test_bucket",
        "s3_url": ""
    }
    store = client.create_store(create_params)
    print(f'Created store: {store}')
    # Remove store
    store_id = store['pk']
    client.delete_store(store_id)
    print(f'Removed store {store_id}')

def test_create_invalid_store():
    print('\nCreating store with invalid bucket type')
    print('================')
    # This should raise BadRequestException
    create_params = {
        "type": "InvalidStore", #invalid bucket type
        "bucket": "empty_bucket",
        "s3_url": ""
    }
    try:
       client.create_store(create_params)
    except BadRequestException as e:
        print(f'BadRequestException: {str(e)}')

def test_create_invalid_store_params():
    print('\nCreating store with invalid params')
    print('================')
    # This should raise BadRequestException
    create_params = {
        "bingo": "bongo" #invalid parameters
    }
    try:
       client.create_store(create_params)
    except BadRequestException as e:
        print(f'BadRequestException: {str(e)}')

def test_create_invalid_bucket_store():
    print('\nCreating invalid bucket store')
    print('================')
    # This should raise BadRequestException
    create_params = {
        "type": "BucketStore",
        "bucket": "test_bucket",
        "s3_url": "" #missing s3_url
    }
    try:
       client.create_store(create_params)
    except BadRequestException as e:
        print(f'BadRequestException: {str(e)}')


####################################
## s3cfgs
####################################

def list_s3cfgs():
    s3cfgs = client.list_s3cfgs()
    print(f'All s3cfgs: {s3cfgs}')

def test_create_update_delete_s3cfg():
    print('\Creating, updating, and deleting s3cfg')
    print('================')
    # Create s3cfg
    original_params = {
        "url": "localhost:8000",
        "access_key": "old1",
        "secret_key": "old2"
    }
    s3cfg = client.create_s3cfg(original_params)
    s3cfg_id = s3cfg['pk']
    print(f'Original s3cfg: {s3cfg}')
    # Update s3cfg
    updated_params = {
        "url": "localhost:8001",
        "access_key": "new1",
        "secret_key": "new2"
    }
    client.update_s3cfg(s3cfg_id, updated_params)
    updated_s3cfg = client.get_s3cfg(s3cfg_id)
    print(f'Updated s3cfg: {updated_s3cfg}')
    # Remove s3cfg to avoid clogging
    s3cfg_id = s3cfg['pk']
    client.delete_s3cfg(s3cfg_id)
    print(f'Removed s3cfg {s3cfg_id}')

def test_create_invalid_s3cfg():
    print('\nCreating invalid s3cfg')
    print('================')
    create_params = {
        "bad_param": "breaking bad"
    }
    try:
        s3cfg = client.create_s3cfg(create_params)
        print(s3cfg)
    except Exception as e:
        print(str(e))


####################################
## Identifiers
####################################

def list_identifiers():
    identifiers = client.list_identifiers()
    print(f'All identifiers: {identifiers}')

def test_create_update_delete_identifier():
    print('\nCreating, updating, and deleting identifier')
    print('================')
    # Create identifier
    original_params = {
        "name": "demo_identifier",
        "pattern": "*foo*"
    }
    identifier = client.create_identifier(original_params)
    identifier_name = identifier['name']
    print(f'Original identifier: {identifier}')
    # Update identifier
    updated_params = {
        "name": "demo_identifier",
        "pattern": "*new foo*"
    }
    client.update_identifier(updated_params)
    updated_identifier = client.get_identifier(identifier_name)
    print(f'Updated identifier: {updated_identifier}')
    # Remove identifier to avoid clogging
    identifier_name = identifier['name']
    client.delete_identifier(identifier_name)
    print(f'Removed identifier {identifier_name}')

def test_create_invalid_identifier():
    print('\nCreating identifier with invalid params')
    print('================')
    # This should raise BadRequestException
    create_params = {
        "whoami": "foo bar" #invalid parameters
    }
    try:
       client.create_identifier(create_params)
    except BadRequestException as e:
        print(f'BadRequestException: {str(e)}')


if __name__ == "__main__":
    # test_media_create()

    test_create_store()
    test_create_invalid_store()
    test_create_invalid_store_params()
    test_create_invalid_bucket_store()

    test_create_update_delete_s3cfg()
    test_create_invalid_s3cfg()

    test_create_update_delete_identifier()
    test_create_invalid_identifier()

    print('\nLists of objects in the mediastore')
    print('================')
    list_stores()
    list_s3cfgs()
    list_identifiers()