from pydantic import ValidationError
from apiclient import ApiClient
from schemas.mediastore import IdentifierTypeSchema, S3ConfigSchemaCreate, S3ConfigSchemaSansKeys, StoreConfigSchema, StoreConfigSchemaCreate
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

def test_create_delete_store():
    print('\nCreating store')
    print('================')
    # Create store
    store = StoreConfigSchemaCreate(
        type = "DictStore",
        bucket = "test_bucket",
        s3_url = ""
    )
    created_store = client.create_store(store).response
    print(f'Created store: {created_store}')
    # Remove store
    created_store_id = created_store['pk']
    client.delete_store(created_store_id)
    print(f'Removed store {created_store_id}')

def test_create_invalid_store():
    print('\nCreating store with invalid bucket type')
    print('================')
    invalid_store = StoreConfigSchemaCreate(
        type = "InvalidStore",
        bucket = "bad_bucket",
        s3_url = ""
    )
    try:
        # This should raise BadRequestException
        client.create_store(invalid_store)
    except BadRequestException as e:
        print(f'BadRequestException: {str(e)}')

def test_create_invalid_bucket_store():
    print('\nCreating invalid bucket store')
    print('================')
    create_params = StoreConfigSchemaCreate(
        type = "BucketStore",
        bucket = "test_bucket",
        s3_url = "" #missing s3_url
    )
    try:
        # This should raise BadRequestException
       client.create_store(create_params)
    except BadRequestException as e:
        print(f'BadRequestException: {str(e)}')

def test_invalid_store_schema():
    print('\nCreating store that will fail schema validation')
    print('================')
    try:
        # This should raise ValidationError
        StoreConfigSchemaCreate(
            bingo = "bongo"
        )
    except ValidationError as e:
        print(f'ValidationError: {str(e)}')


####################################
## s3cfgs
####################################

def list_s3cfgs():
    s3cfgs = client.list_s3cfgs()
    print(f'All s3cfgs: {s3cfgs}')

def test_create_update_delete_s3cfg():
    print('\nCreating, updating, and deleting s3cfg')
    print('================')
    # Create s3cfg
    original_s3cfg = S3ConfigSchemaCreate(
        url = "localhost:8000",
        access_key = "old1",
        secret_key = "old2"
    )
    s3cfg = client.create_s3cfg(original_s3cfg).response
    s3cfg_id = s3cfg['pk']
    print(f'Original s3cfg: {s3cfg}')
    # Update s3cfg
    updated_s3cfg = S3ConfigSchemaCreate(
        url = "localhost:8001",
        access_key = "new1",
        secret_key = "new2"
    )
    client.update_s3cfg(s3cfg_id, updated_s3cfg)
    retrieved_updated_s3cfg = client.get_s3cfg(s3cfg_id).response
    print(f'Updated s3cfg: {retrieved_updated_s3cfg}')
    # Remove s3cfg to avoid clogging
    retrieved_updated_s3cfg_id = retrieved_updated_s3cfg['pk']
    client.delete_s3cfg(retrieved_updated_s3cfg_id)
    print(f'Removed s3cfg {retrieved_updated_s3cfg_id}')

def test_invalid_s3cfg_schema():
    print('\nCreating invalid s3cfg')
    print('================')
    try:
        # This should raise ValidationError
        S3ConfigSchemaCreate(
            bad_param = "breaking bad"
        )
    except ValidationError as e:
        print(f'ValidationError: {str(e)}')


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
    original_identifier = IdentifierTypeSchema(
        name = "demo_identifier",
        pattern = "*foo*"
    )
    identifier = client.create_identifier(original_identifier).response
    identifier_name = identifier['name']
    print(f'Original identifier: {identifier}')
    # Update identifier
    updated_identifier = IdentifierTypeSchema(
        name = "demo_identifier",
        pattern = "*new foo*"
    )
    client.update_identifier(updated_identifier)
    retrieved_updated_identifier = client.get_identifier(identifier_name).response
    print(f'Updated identifier: {retrieved_updated_identifier}')
    # Remove identifier to avoid clogging
    retrieved_updated_identifier_name = retrieved_updated_identifier['name']
    client.delete_identifier(retrieved_updated_identifier_name)
    print(f'Removed identifier {retrieved_updated_identifier_name}')

def test_create_invalid_identifier():
    print('\nCreating identifier with invalid params')
    print('================')
    try:
        # This should raise ValidationError
        IdentifierTypeSchema(
            whoami = "an invalid value"
        )
    except ValidationError as e:
        print(f'ValidationError: {str(e)}')


if __name__ == "__main__":
    # test_media_create()

    test_create_delete_store()
    test_create_invalid_store()
    test_create_invalid_bucket_store()
    test_invalid_store_schema()

    test_create_update_delete_s3cfg()
    test_invalid_s3cfg_schema()

    test_create_update_delete_identifier()
    test_create_invalid_identifier()

    print('\nLists of objects in the mediastore')
    print('================')
    list_stores()
    list_s3cfgs()
    list_identifiers()