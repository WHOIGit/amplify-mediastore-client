from apiclient import ApiClient
from dotenv import load_dotenv
from pprint import pprint
from schemas.mediastore import IdentifierTypeSchema, MediaSchema, MediaSchemaCreate, MediaSchemaUpdate, MediaSchemaUpdateIdentifiers, MediaSchemaUpdateMetadata, MediaSchemaUpdateStorekey, MediaSchemaUpdateTags, MediaSearchSchema, S3ConfigSchemaCreate, S3ConfigSchemaSansKeys, StoreConfigSchema, StoreConfigSchemaCreate, UploadSchemaInput
from utils.custom_exception import ClientError, ServerError
import base64
import os
import unittest
import uuid

class BaseTestCase(unittest.TestCase):
    """Base class providing common test infrastructure"""

    @classmethod
    def setUpClass(cls):
        """One-time setup for the test class"""
        super().setUpClass()
        load_dotenv()
        cls.base_url = os.environ.get("AMPLIFY_MEDIASTORE_CLIENT_URL")
        cls.credentials = {
            "username": os.environ.get('AMPLIFY_MEDIASTORE_CLIENT_USERNAME'),
            "password": os.environ.get('AMPLIFY_MEDIASTORE_CLIENT_PASSWORD')
        }

    def setUp(self):
        """Reinstantiate client before each test method"""
        self.client = ApiClient(
            base_url=self.base_url,
            username=self.credentials["username"],
            password=self.credentials["password"]
        )
        self._resources_to_cleanup = []

    def tearDown(self):
        """Remove resources after after each test"""
        for cleanup_func in reversed(self._resources_to_cleanup):
            try:
                cleanup_func()
            except Exception as e:
                print(f'Cleanup failed: {e}')

    def add_cleanup(self, cleanup_func):
        """Register a resource for cleanup"""
        self._resources_to_cleanup.append(cleanup_func)

class TestHelpers:
    """Helper methods for creating and managing test resources"""

    @staticmethod
    def generate_test_url() -> str:
        return f"http://{uuid.uuid4()}:1234"

    @staticmethod
    def generate_test_keys() -> tuple[str, str]:
        test_id = str(uuid.uuid4())
        return f"test_access_{test_id}", f"test_secret_{test_id}"

    @staticmethod
    def generate_test_pattern() -> str:
        return f"^test_pattern_{uuid.uuid4()}$"

    @staticmethod
    def generate_test_pid() -> str:
        return f"test_pid_{uuid.uuid4()}"

    @staticmethod
    def generate_test_tags() -> list:
        return [f"tag_{uuid.uuid4()}", "test_tag", "media_test"]

    @staticmethod
    def generate_test_metadata() -> dict:
        return {
            "title": f"Test Media {uuid.uuid4()}",
            "description": "Test description",
            "created": "2024-01-01T00:00:00Z"
        }

    @classmethod
    def create_s3_config(cls, client: ApiClient) -> tuple[dict, callable]:
        """
        Create an S3 configuration for testing
        Returns:
            tuple: (created config dict, cleanup function)
        """
        access_key, secret_key = cls.generate_test_keys()
        config = S3ConfigSchemaCreate(
            url=cls.generate_test_url(),
            access_key=access_key,
            secret_key=secret_key
        )

        response = client.create_s3cfg(config)
        created_config = response.response

        cleanup = lambda: client.delete_s3cfg(created_config['pk'])
        return created_config, cleanup

    @classmethod
    def create_identifier(cls, client: ApiClient) -> tuple[dict, callable]:
        """
        Create an identifier for testing
        Returns:
            tuple: (created identifier dict, cleanup function)
        """
        test_id = str(uuid.uuid4())
        identifier = IdentifierTypeSchema(
            name=f"test_identifier_{test_id}",
            pattern=cls.generate_test_pattern()
        )

        response = client.create_identifier(identifier)
        created_identifier = response.response

        cleanup = lambda: client.delete_identifier(created_identifier['name'])
        return created_identifier, cleanup

    @classmethod
    def create_store(cls, client: ApiClient, store_type: str = "DictStore", s3_url: str = None) -> tuple[dict, callable]:
        """
        Create a store configuration for testing
        Args:
            store_type: Type of store to create
        Returns:
            tuple: (created store dict, cleanup function)
        """
        test_id = str(uuid.uuid4())
        bucket = f"test_bucket_{test_id}"

        config_params = {
            "type": store_type,
            "bucket": bucket
        }

        if s3_url:
            config_params['s3_url'] = s3_url

        store_config = StoreConfigSchemaCreate(**config_params)
        response = client.create_store(store_config)
        created_store = response.response

        cleanup = lambda: client.delete_store(created_store['pk'])
        return created_store, cleanup

    @classmethod
    def create_test_media(cls, client: ApiClient) -> tuple[dict, callable, callable, callable]:
        """
        Create a media item for testing
        Returns:
            tuple: (created media dict, media cleanup func, store cleanup func, identifier cleanup func)
        """
        store, store_cleanup = cls.create_store(client)
        pid_identifier, pid_identifier_cleanup = cls.create_identifier(client)
        test_identifier, test_identifier_cleanup = cls.create_identifier(client)

        identifiers = {test_identifier['name']: test_identifier['pattern']}

        media_data = MediaSchemaCreate(
            pid=cls.generate_test_pid(),
            pid_type=pid_identifier['name'],
            store_config=store,
            metadata=cls.generate_test_metadata(),
            tags=cls.generate_test_tags(),
            identifiers=identifiers
        )

        response = client.create_media_single(media_data)
        created_media = response.response

        media_cleanup = lambda: client.delete_media_by_pid(created_media['pid'])

        def identifier_cleanup():
            pid_identifier_cleanup()
            test_identifier_cleanup()

        return created_media, media_cleanup, store_cleanup, identifier_cleanup

    @classmethod
    def create_upload(cls, client: ApiClient, base64_content: bool = True) -> tuple[dict, callable]:
        test_media, media_cleanup, store_cleanup, identifier_cleanup = cls.create_test_media(client)
        test_content = b'test content for upload'
        base64_test_content = base64.b64encode(test_content).decode('ascii') if base64_content else ''

        upload = UploadSchemaInput(
            mediadata=test_media,
            base64=base64_test_content
        )

        def cleanup():
            media_cleanup()
            store_cleanup()
            identifier_cleanup()

        return upload, cleanup

class S3ConfigTest(BaseTestCase):
    """Test cases for S3 configuration management"""

    def test_create_s3_config(self):
        """Test creating a new S3 configuration"""
        test_url = TestHelpers.generate_test_url()
        access_key, secret_key = TestHelpers.generate_test_keys()
        config = S3ConfigSchemaCreate(
            url=test_url,
            access_key=access_key,
            secret_key=secret_key
        )

        response = self.client.create_s3cfg(config)

        self.assertEqual(response.status_code, 200)
        created_config = response.response
        self.assertIn('pk', created_config)
        self.assertEqual(created_config['url'], test_url)

        self.add_cleanup(lambda: self.client.delete_s3cfg(created_config['pk']))

    def test_update_s3_config(self):
        """Test updating an S3 configuration"""
        config, cleanup = TestHelpers.create_s3_config(self.client)
        self.add_cleanup(cleanup)

        new_access_key, new_secret_key = TestHelpers.generate_test_keys()
        updated_config = S3ConfigSchemaCreate(
            url=config['url'],
            access_key=new_access_key,
            secret_key=new_secret_key
        )

        response = self.client.update_s3cfg(config['pk'], updated_config)
        self.assertEqual(response.status_code, 204)

        # Verify the update
        get_response = self.client.get_s3cfg(config['pk'])
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.response['url'], config['url'])

    def test_update_s3_config(self):
        """Test updating an S3 configuration"""
        config, cleanup = TestHelpers.create_s3_config(self.client)
        self.add_cleanup(cleanup)

        new_access_key, new_secret_key = TestHelpers.generate_test_keys()
        updated_config = S3ConfigSchemaCreate(
            url=config['url'],
            access_key=new_access_key,
            secret_key=new_secret_key
        )

        response = self.client.update_s3cfg(config['pk'], updated_config)
        self.assertEqual(response.status_code, 204)

    def test_delete_s3_config(self):
        """Test deleting an S3 configuration"""
        config, _ = TestHelpers.create_s3_config(self.client)
        response = self.client.delete_s3cfg(config['pk'])
        self.assertEqual(response.status_code, 204)

    def test_list_s3_configs(self):
        """Test listing S3 configurations"""
        config1, cleanup1 = TestHelpers.create_s3_config(self.client)
        config2, cleanup2 = TestHelpers.create_s3_config(self.client)
        self.add_cleanup(cleanup1)
        self.add_cleanup(cleanup2)

        response = self.client.list_s3cfgs()

        self.assertEqual(response.status_code, 200)
        configs = response.response
        self.assertIsInstance(configs, list)
        config_pks = {cfg['pk'] for cfg in configs}
        self.assertIn(config1['pk'], config_pks)
        self.assertIn(config2['pk'], config_pks)

    def test_create_duplicate_s3_config(self):
        """Test creating S3 config with duplicate URL fails"""
        config, cleanup = TestHelpers.create_s3_config(self.client)
        self.add_cleanup(cleanup)

        duplicate_config = S3ConfigSchemaCreate(
            url=config['url'],
            access_key="new_access",
            secret_key="new_secret"
        )

        with self.assertRaises(Exception):
            self.client.create_s3cfg(duplicate_config)

class IdentifierTest(BaseTestCase):
    def test_create_identifier(self):
        """Test creating a new identifier"""
        test_id = str(uuid.uuid4())
        identifier = IdentifierTypeSchema(
            name=f"test_identifier_{test_id}",
            pattern=TestHelpers.generate_test_pattern()
        )

        response = self.client.create_identifier(identifier)

        self.assertEqual(response.status_code, 200)
        created_identifier = response.response
        self.assertEqual(created_identifier['name'], identifier.name)
        self.assertEqual(created_identifier['pattern'], identifier.pattern)

        self.add_cleanup(lambda: self.client.delete_identifier(created_identifier['name']))

    def test_update_identifier(self):
        """Test updating an identifier"""
        identifier, cleanup = TestHelpers.create_identifier(self.client)
        self.add_cleanup(cleanup)

        updated_pattern = TestHelpers.generate_test_pattern()
        updated_identifier = IdentifierTypeSchema(
            name=identifier['name'],
            pattern=updated_pattern
        )

        response = self.client.update_identifier(updated_identifier)
        self.assertEqual(response.status_code, 204)

        # Verify the update
        get_response = self.client.get_identifier(identifier['name'])
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.response['pattern'], updated_pattern)

    def test_delete_identifier(self):
        """Test deleting an identifier"""
        identifier, _ = TestHelpers.create_identifier(self.client)
        response = self.client.delete_identifier(identifier['name'])
        self.assertEqual(response.status_code, 204)

        # Verify deletion by attempting to get the identifier
        with self.assertRaises(Exception):
            self.client.get_identifier(identifier['name'])

    def test_list_identifiers(self):
        """Test listing identifiers"""
        identifier1, cleanup1 = TestHelpers.create_identifier(self.client)
        identifier2, cleanup2 = TestHelpers.create_identifier(self.client)
        self.add_cleanup(cleanup1)
        self.add_cleanup(cleanup2)

        response = self.client.list_identifiers()

        self.assertEqual(response.status_code, 200)
        identifiers = response.response
        self.assertIsInstance(identifiers, list)
        identifier_names = {identifier['name'] for identifier in identifiers}
        self.assertIn(identifier1['name'], identifier_names)
        self.assertIn(identifier2['name'], identifier_names)

    def test_create_duplicate_identifier(self):
        """Test creating identifier with duplicate name fails"""
        identifier, cleanup = TestHelpers.create_identifier(self.client)
        self.add_cleanup(cleanup)

        duplicate_identifier = IdentifierTypeSchema(
            name=identifier['name'],
            pattern=TestHelpers.generate_test_pattern()
        )

        with self.assertRaises(Exception):
            self.client.create_identifier(duplicate_identifier)

    def test_get_nonexistent_identifier(self):
        """Test getting a non-existent identifier fails"""
        with self.assertRaises(Exception):
            self.client.get_identifier(f"nonexistent_{uuid.uuid4()}")

class StoreTest(BaseTestCase):
    def test_create_store(self):
        """Test creating a new dict store configuration"""
        store_config = StoreConfigSchemaCreate(
            type = "DictStore",
            bucket = f"test_bucket_{uuid.uuid4()}"
        )

        response = self.client.create_store(store_config)

        self.assertEqual(response.status_code, 200)
        created_store = response.response
        self.assertIn('pk', created_store)
        self.assertEqual(created_store['type'], store_config.type)
        self.assertEqual(created_store['bucket'], store_config.bucket)
        self.assertEqual(created_store['s3_url'], '')

        self.add_cleanup(lambda: self.client.delete_store(created_store['pk']))

    def test_create_bucket_store(self):
        """Test creating a new bucket store configuration with S3"""
        # First create S3 config
        s3config, s3_cleanup = TestHelpers.create_s3_config(self.client)
        self.add_cleanup(s3_cleanup)

        store_config = StoreConfigSchemaCreate(
            type = "BucketStore",
            bucket = f"test_bucket_{uuid.uuid4()}",
            s3_url = s3config['url']
        )

        response = self.client.create_store(store_config)

        self.assertEqual(response.status_code, 200)
        created_store = response.response
        self.assertIn('pk', created_store)
        self.assertEqual(created_store['type'], store_config.type)
        self.assertEqual(created_store['bucket'], store_config.bucket)
        self.assertEqual(created_store['s3_url'], s3config['url'])

        self.add_cleanup(lambda: self.client.delete_store(created_store['pk']))

    def test_create_bucket_store_without_s3_fails(self):
        """Test creating a bucket store without S3 config fails"""
        store_config = StoreConfigSchemaCreate(
            type="BucketStore",
            bucket=f"test_bucket_{uuid.uuid4()}",
        )

        with self.assertRaises(Exception):
            self.client.create_store(store_config)

    def test_create_filesystem_store_with_s3_fails(self):
        """Test creating a filesystem store with S3 config fails"""
        s3config, s3_cleanup = TestHelpers.create_s3_config(self.client)
        self.add_cleanup(s3_cleanup)

        store_config = StoreConfigSchemaCreate(
            type = "FilesystemStore",
            bucket = f"test_bucket_{uuid.uuid4()}",
            s3_url = s3config['url']
        )

        with self.assertRaises(Exception):
            self.client.create_store(store_config)

    def test_create_invalid_store_type(self):
        """Test creating store with invalid type fails"""
        store_config = StoreConfigSchemaCreate(
            type = "InvalidStore",
            bucket = f"test_bucket_{uuid.uuid4()}"
        )

        with self.assertRaises(ClientError):
            self.client.create_store(store_config)

    def test_get_store(self):
        """Test getting a store configuration"""
        store, cleanup = TestHelpers.create_store(self.client)
        self.add_cleanup(cleanup)

        response = self.client.get_store(store['pk'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.response['pk'], store['pk'])
        self.assertEqual(response.response['type'], store['type'])
        self.assertEqual(response.response['bucket'], store['bucket'])

    def test_delete_store(self):
        """Test deleting a store configuration"""
        store, _ = TestHelpers.create_store(self.client)

        response = self.client.delete_store(store['pk'])
        self.assertEqual(response.status_code, 204)

        # Verify deletion
        with self.assertRaises(Exception):
            self.client.get_store(store['pk'])

    def test_list_stores(self):
        """Test listing store configurations"""
        store1, cleanup1 = TestHelpers.create_store(self.client, "FilesystemStore")
        store2, cleanup2 = TestHelpers.create_store(self.client, "DictStore")
        self.add_cleanup(cleanup1)
        self.add_cleanup(cleanup2)

        response = self.client.list_stores()

        self.assertEqual(response.status_code, 200)
        stores = response.response
        self.assertIsInstance(stores, list)
        store_pks = {store['pk'] for store in stores}
        self.assertIn(store1['pk'], store_pks)
        self.assertIn(store2['pk'], store_pks)

class MediaTest(BaseTestCase):
    def test_create_media_single(self):
        """Test creating a single media item"""
        store, store_cleanup = TestHelpers.create_store(self.client)
        identifier, identifier_cleanup = TestHelpers.create_identifier(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)

        media_data = MediaSchemaCreate(
            pid=TestHelpers.generate_test_pid(),
            pid_type=identifier['name'],
            store_config=store,
            metadata=TestHelpers.generate_test_metadata(),
            tags=TestHelpers.generate_test_tags()
        )

        response = self.client.create_media_single(media_data)

        self.assertEqual(response.status_code, 200)
        created_media = response.response
        self.assertEqual(created_media['pid'], media_data.pid)
        self.assertEqual(created_media['pid_type'], media_data.pid_type)
        self.assertEqual(created_media['metadata'], media_data.metadata)
        self.assertEqual(created_media['tags'], media_data.tags)

        self.add_cleanup(lambda: self.client.delete_media_by_pid(created_media['pid']))

    def test_create_media_single_invalid_data(self):
        """Test creating media with invalid data fails appropriately"""
        invalid_media = MediaSchemaCreate(
            pid="",  # Invalid empty PID
            pid_type="TEST",
            store_config=StoreConfigSchemaCreate(
                type="InvalidStore",  # Invalid store type
                bucket="test_bucket"
            )
        )

        with self.assertRaises(ClientError):
            self.client.create_media_single(invalid_media)

    def test_get_media_by_pid(self):
        """Test retrieving media by PID"""
        media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        # Must be in this order, the media object must be deleted first
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)
        self.add_cleanup(media_cleanup)

        response = self.client.get_media_by_pid(media['pid'])

        self.assertEqual(response.status_code, 200)
        retrieved_media = response.response
        self.assertEqual(retrieved_media['pid'], media['pid'])
        self.assertEqual(retrieved_media['metadata'], media['metadata'])
        self.assertEqual(retrieved_media['tags'], media['tags'])

    def test_get_media_nonexistent_pid(self):
        """Test getting media with non-existent PID fails appropriately"""
        with self.assertRaises(ServerError):
            self.client.get_media_by_pid(f"nonexistent_{uuid.uuid4()}")

    def test_delete_media_by_pid(self):
        """Test deleting media by PID"""
        media, _, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)

        response = self.client.delete_media_by_pid(media['pid'])
        self.assertEqual(response.status_code, 204)

        # Verify deletion
        with self.assertRaises(ServerError):
            self.client.get_media_by_pid(media['pid'])

    def test_update_single_media(self):
        media, _, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)

        new_pid = TestHelpers.generate_test_pid()
        update_data = MediaSchemaUpdate(
            pid=media['pid'],
            new_pid=new_pid,
            pid_type=media['pid_type']
        )

        response = self.client.update_single_media(media['pid'], update_data)
        self.assertEqual(response.status_code, 204)

        # Verify update
        updated_response = self.client.get_media_by_pid(new_pid)
        updated_media = updated_response.response
        self.assertEqual(updated_media['pid'], new_pid)

        # Custom cleanup for the new PID
        self.add_cleanup(lambda: self.client.delete_media_by_pid(new_pid))

    def test_create_bulk_media(self):
        """Test creating multiple media items in bulk"""
        store, store_cleanup = TestHelpers.create_store(self.client)
        identifier, identifier_cleanup = TestHelpers.create_identifier(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)

        media_items = []
        for _ in range(3):
            media_items.append(MediaSchemaCreate(
                pid=TestHelpers.generate_test_pid(),
                pid_type=identifier['name'],
                store_config=StoreConfigSchemaCreate(
                    type=store['type'],
                    bucket=store['bucket']
                ),
                metadata=TestHelpers.generate_test_metadata(),
                tags=TestHelpers.generate_test_tags()
            ))

        response = self.client.create_bulk_media(media_items)

        self.assertEqual(response.status_code, 200)
        created_items = response.response
        self.assertEqual(len(created_items), len(media_items))

        # Add cleanup for created items
        for item in created_items:
            self.add_cleanup(lambda pid=item['pid']: self.client.delete_media_by_pid(pid))

    def test_read_bulk_media(self):
        """Test retrieving multiple media items in bulk"""
        media1, media_cleanup_1, store_cleanup_1, identifier_cleanup_1 = TestHelpers.create_test_media(self.client)
        media2, media_cleanup_2, store_cleanup_2, identifier_cleanup_2 = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup_1)
        self.add_cleanup(identifier_cleanup_1)
        self.add_cleanup(media_cleanup_1)
        self.add_cleanup(store_cleanup_2)
        self.add_cleanup(identifier_cleanup_2)
        self.add_cleanup(media_cleanup_2)

        pid_list = [media1['pid'], media2['pid']]
        response = self.client.read_bulk_media(pid_list)

        self.assertEqual(response.status_code, 200)
        retrieved_items = response.response
        self.assertEqual(len(retrieved_items), 2)
        retrieved_pids = [item['pid'] for item in retrieved_items]
        self.assertIn(media1['pid'], retrieved_pids)
        self.assertIn(media2['pid'], retrieved_pids)

    def test_search_bulk_media(self):
        """Test searching media items"""
        media1, media_cleanup_1, store_cleanup_1, identifier_cleanup_1 = TestHelpers.create_test_media(self.client)
        media2, media_cleanup_2, store_cleanup_2, identifier_cleanup_2 = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup_1)
        self.add_cleanup(identifier_cleanup_1)
        self.add_cleanup(media_cleanup_1)
        self.add_cleanup(store_cleanup_2)
        self.add_cleanup(identifier_cleanup_2)
        self.add_cleanup(media_cleanup_2)

        media1_specific_tag = media1['tags'][0]
        search_params = MediaSearchSchema(tags=[media1_specific_tag])
        response = self.client.search_bulk_media(search_params)

        self.assertEqual(response.status_code, 200)
        search_results = response.response

        self.assertTrue(any(media['pid'] == media1['pid'] for media in search_results))
        self.assertFalse(any(media['pid'] == media2['pid'] for media in search_results))

    def test_delete_bulk_media(self):
        """Test deleting multiple media items in bulk"""
        media1, _, store_cleanup_1, identifier_cleanup_1 = TestHelpers.create_test_media(self.client)
        media2, _, store_cleanup_2, identifier_cleanup_2 = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup_1)
        self.add_cleanup(identifier_cleanup_1)
        self.add_cleanup(store_cleanup_2)
        self.add_cleanup(identifier_cleanup_2)

        pid_list = [media1['pid'], media2['pid']]
        response = self.client.delete_bulk_media(pid_list)

        self.assertEqual(response.status_code, 200)

        # Verify deletion
        for pid in pid_list:
            with self.assertRaises(ServerError):
                self.client.get_media_by_pid(pid)

    # def test_update_bulk_media(self):
    #     """Test updating multiple media items in bulk"""
    #     media1, _, store_cleanup_1, identifier_cleanup_1 = TestHelpers.create_test_media(self.client)
    #     media2, _, store_cleanup_2, identifier_cleanup_2 = TestHelpers.create_test_media(self.client)
    #     self.add_cleanup(store_cleanup_1)
    #     self.add_cleanup(identifier_cleanup_1)
    #     self.add_cleanup(store_cleanup_2)
    #     self.add_cleanup(identifier_cleanup_2)

    #     old_pids = [media1['pid'], media2['pid']]
    #     new_pids = [f"{pid}_updated" for pid in old_pids]

    #     for pid in new_pids:
    #         self.add_cleanup(lambda p=pid: self.client.delete_media_by_pid(p))

    #     updates = [
    #         MediaSchemaUpdate(
    #             pid=old_pids[0],
    #             new_pid=new_pids[0],
    #             pid_type=media1['pid_type']
    #         ),
    #         MediaSchemaUpdate(
    #             pid=old_pids[1],
    #             new_pid=new_pids[1],
    #             pid_type=media2['pid_type']
    #         )
    #     ]

    #     response = self.client.update_bulk_media(updates)
    #     self.assertEqual(response.status_code, 204)

    #     # Verify old PIDs don't exist
    #     for old_pid in old_pids:
    #         with self.assertRaises(ClientError):
    #             self.client.get_media_by_pid(old_pid)

    #     # Verify new PIDs exist and have correct data
    #     response = self.client.get_media_by_pid(new_pids[0])
    #     self.assertEqual(response.status_code, 200)
    #     updated_media = response.response
    #     self.assertEqual(updated_media['pid'], new_pids[0])
    #     self.assertEqual(updated_media['pid_type'], media1['pid_type'])
    #     self.assertEqual(updated_media['metadata'], media1['metadata'])
    #     self.assertEqual(updated_media['tags'], media1['tags'])

    #     response = self.client.get_media_by_pid(new_pids[1])
    #     self.assertEqual(response.status_code, 200)
    #     updated_media = response.response
    #     self.assertEqual(updated_media['pid_type'], media2['pid_type'])
    #     self.assertEqual(updated_media['metadata'], media2['metadata'])
    #     self.assertEqual(updated_media['tags'], media2['tags'])

class MediaAttributesTest(BaseTestCase):
    def test_patch_media_tags(self):
        """Test partial update of media tags"""
        media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)
        self.add_cleanup(media_cleanup)
        initial_tags = media['tags']
        new_tags = [f"new_tag_{uuid.uuid4()}", "extra_test_tag"]
        update = MediaSchemaUpdateTags(
            pid=media['pid'],
            tags=new_tags
        )

        response = self.client.patch_media_tags([update])
        self.assertEqual(response.status_code, 200)

        # Verify update
        updated = self.client.get_media_by_pid(media['pid']).response
        self.assertTrue(all(tag in updated['tags'] for tag in initial_tags))
        self.assertTrue(all(tag in updated['tags'] for tag in new_tags))

    def test_update_media_tags(self):
        """Test complete replacement of media tags"""
        media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)
        self.add_cleanup(media_cleanup)

        new_tags = [f"replacement_tag_{uuid.uuid4()}", "test_tag_new"]
        update = MediaSchemaUpdateTags(
            pid=media['pid'],
            tags=new_tags
        )

        response = self.client.update_media_tags([update])
        self.assertEqual(response.status_code, 200)

        # Verify update
        updated = self.client.get_media_by_pid(media['pid']).response
        self.assertEqual(sorted(updated['tags']), sorted(new_tags))
        self.assertFalse(any(tag in updated['tags'] for tag in media['tags']))

    def test_update_media_storekeys(self):
        """Test updating store keys"""
        media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)
        self.add_cleanup(media_cleanup)

        new_storekey = f"new_storekey_{uuid.uuid4()}"
        update = MediaSchemaUpdateStorekey(
            pid=media['pid'],
            store_key=new_storekey
        )

        response = self.client.update_media_storekeys([update])
        self.assertEqual(response.status_code, 200)

    def test_update_media_identifiers(self):
        """Test updating media identifiers"""
        media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)
        self.add_cleanup(media_cleanup)

        new_identifier, new_identifier_cleanup = TestHelpers.create_identifier(self.client)
        self.add_cleanup(new_identifier_cleanup)
        new_identifiers = {new_identifier['name']: new_identifier['pattern']}

        update = MediaSchemaUpdateIdentifiers(
            pid=media['pid'],
            identifiers=new_identifiers
        )

        response = self.client.update_media_identifiers([update])
        self.assertEqual(response.status_code, 200)

        # Verify update
        updated = self.client.get_media_by_pid(media['pid']).response
        self.assertEqual(updated['identifiers'], new_identifiers)

    def test_update_media_metadata(self):
        """Test complete replacement of metadata"""
        media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)
        self.add_cleanup(media_cleanup)

        new_metadata = {
            "new_field": "new_value"
        }
        update = MediaSchemaUpdateMetadata(
            pid=media['pid'],
            data=new_metadata
        )

        response = self.client.update_media_metadata([update])
        self.assertEqual(response.status_code, 200)

        # Verify update
        updated = self.client.get_media_by_pid(media['pid']).response
        self.assertEqual(updated['metadata'], new_metadata)
        self.assertFalse(any(key in updated['metadata'] for key in media['metadata']))

    def test_patch_media_metadata(self):
        """Test partial update of metadata"""
        media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)
        self.add_cleanup(media_cleanup)

        new_metadata = {
            "new_field": "new_value",
            "another_field": "another_value"
        }
        update = MediaSchemaUpdateMetadata(
            pid=media['pid'],
            data=new_metadata
        )

        response = self.client.patch_media_metadata([update])
        self.assertEqual(response.status_code, 200)

        # Verify update
        updated = self.client.get_media_by_pid(media['pid']).response
        # Original metadata should still be present
        self.assertTrue(all(
            media['metadata'][key] == updated['metadata'][key]
            for key in media['metadata']
        ))
        # New metadata should be added
        self.assertTrue(all(
            new_metadata[key] == updated['metadata'][key]
            for key in new_metadata
        ))

    def test_delete_media_metadata(self):
        """Test deletion of specific metadata fields"""
        media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
        self.add_cleanup(store_cleanup)
        self.add_cleanup(identifier_cleanup)
        self.add_cleanup(media_cleanup)

        additional_metadata = {
            "to_delete": "value1",
            "keep_this": "value2"
        }
        add_update = [
            MediaSchemaUpdateMetadata(
                pid=media['pid'],
                data=additional_metadata
            )
        ]
        self.client.patch_media_metadata(add_update)

        delete_update = [
            MediaSchemaUpdateMetadata(
                pid=media['pid'],
                keys=['to_delete']
            )
        ]

        response = self.client.delete_media_metadata(delete_update)
        self.assertEqual(response.status_code, 200)

        # Verify update
        updated = self.client.get_media_by_pid(media['pid']).response
        self.assertNotIn("to_delete", updated['metadata'])
        self.assertIn("keep_this", updated['metadata'])
        self.assertEqual(updated['metadata']["keep_this"], "value2")

# class UploadDownloadTest(BaseTestCase):
#     def test_upload_media_with_base64(self):
#         """Test uploading media with base64 content"""
#         upload, upload_cleanup = TestHelpers.create_upload(self.client)
#         self.add_cleanup(upload_cleanup)

#         response = self.client.upload_media(upload)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.response['status'], 'READY')

#     def test_upload_media_without_base64(self):
#         """Test uploading media to get presigned URL"""
#         upload, upload_cleanup = TestHelpers.create_upload(self.client, base64_content=False)
#         self.add_cleanup(upload_cleanup)

#         response = self.client.upload_media(upload)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.response['status'], 'PENDING')
#         self.assertIn('presigned_put', response.response)

#     def test_get_download_media_urls_bulk(self):
#         """Test getting download URLs for multiple media objects"""
#         media1, media_cleanup1, store_cleanup1, identifier_cleanup1 = TestHelpers.create_test_media(self.client)
#         media2, media_cleanup2, store_cleanup2, identifier_cleanup2 = TestHelpers.create_test_media(self.client)

#         self.add_cleanup(media_cleanup1)
#         self.add_cleanup(store_cleanup1)
#         self.add_cleanup(identifier_cleanup1)
#         self.add_cleanup(media_cleanup2)
#         self.add_cleanup(store_cleanup2)
#         self.add_cleanup(identifier_cleanup2)

#         pid_list = [media1['pid'], media2['pid']]
#         response = self.client.get_download_media_urls(pid_list)

#         self.assertEqual(response.status_code, 200)
#         self.assertIsInstance(response.response, list)
#         self.assertEqual(len(response.response), 2)

#     def test_get_download_media_url_single(self):
#         """Test getting download URL for a single media object"""
#         media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
#         self.add_cleanup(media_cleanup)
#         self.add_cleanup(store_cleanup)
#         self.add_cleanup(identifier_cleanup)

#         response = self.client.get_download_media_url(media['pid'])

#         self.assertEqual(response.status_code, 200)
#         self.assertIn('mediadata', response.response)
#         self.assertEqual(response.response['mediadata']['pid'], media['pid'])

#     def test_get_download_media_direct(self):
#         """Test direct media download"""
#         media, media_cleanup, store_cleanup, identifier_cleanup = TestHelpers.create_test_media(self.client)
#         self.add_cleanup(media_cleanup)
#         self.add_cleanup(store_cleanup)
#         self.add_cleanup(identifier_cleanup)

#         response = self.client.get_download_media(media['pid'])

#         self.assertEqual(response.status_code, 200)
#         self.assertIn('mediadata', response.response)
#         self.assertEqual(response.response['mediadata']['pid'], media['pid'])

#     def test_download_nonexistent_media(self):
#         """Test handling of non-existent media download"""
#         nonexistent_pid = f"nonexistent_{uuid.uuid4()}"

#         with self.assertRaises(ClientError) as context:
#             self.client.get_download_media(nonexistent_pid)

if __name__ == "__main__":
    # Run all tests
    unittest.main()

    # Run only one class of tests
    # suite = unittest.TestLoader().loadTestsFromTestCase(MediaTest)
    # unittest.TextTestRunner().run(suite)