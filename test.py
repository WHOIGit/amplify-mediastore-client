from apiclient import ApiClient
from pprint import pprint
from pydantic import ValidationError
from schemas.mediastore import IdentifierTypeSchema, MediaSchema, MediaSchemaCreate, MediaSearchSchema, S3ConfigSchemaCreate, S3ConfigSchemaSansKeys, StoreConfigSchema, StoreConfigSchemaCreate
from utils.custom_exception import ClientError
import time
import unittest

# Usage Example

client = ApiClient(base_url="https://amplify-mediastore.whoi.edu", username="sa-mediastore", password="welcometo_homeofthe_")

##############
## Unittest ##
##############

client = ApiClient(base_url="https://amplify-mediastore.whoi.edu", username="sa-mediastore", password="welcometo_homeofthe_")

class StoreTest(unittest.TestCase):
    def test_create_delete_store(self):
        # Create store
        store = StoreConfigSchemaCreate(
            type = "DictStore",
            bucket = "test_bucket",
            s3_url = ""
        )
        created_store = client.create_store(store).response
        self.assertIsNotNone(created_store)
        self.assertIn('pk', created_store)
        self.assertEqual('DictStore', created_store['type'])
        self.assertEqual('test_bucket', created_store['bucket'])
        # Remove store
        delete_response_status = client.delete_store(created_store['pk']).status_code
        self.assertEqual(204, delete_response_status)

    def test_create_invalid_store(self):
        invalid_store = StoreConfigSchemaCreate(
            type = "InvalidStore", #invalid bucket type
            bucket = "bad_bucket",
            s3_url = ""
        )
        # This should raise  ClientError
        with self.assertRaises( ClientError):
            client.create_store(invalid_store)

    def test_create_bad_bucket_store(self):
        # This should raise  ClientError
        invalid_bucket_store = StoreConfigSchemaCreate(
            type = "BucketStore",
            bucket = "test_bucket",
            s3_url = "" #missing s3_url
        )
        # This should raise  ClientError
        with self.assertRaises( ClientError):
            client.create_store(invalid_bucket_store)

    def test_invalid_store_schema(self):
        # This will fail schema validation
        with self.assertRaises(ValidationError):
            StoreConfigSchemaCreate(
                bingo = "bongo"
            )

class S3cfgTest(unittest.TestCase):
    def list_s3cfgs(self):
        return client.list_s3cfgs()

    def test_create_update_delete_s3cfg(self):
        # Create s3cfg
        original_s3cfg = S3ConfigSchemaCreate(
            url = "localhost:8000",
            access_key = "old1",
            secret_key = "old2"
        )
        created_s3cfg = client.create_s3cfg(original_s3cfg).response
        self.assertIsNotNone(created_s3cfg)
        self.assertIn('pk', created_s3cfg)
        self.assertEqual('localhost:8000', created_s3cfg['url'])
        s3cfg_id = created_s3cfg['pk']
        # Update s3cfg
        updated_s3cfg = S3ConfigSchemaCreate(
            url = "localhost:8001",
            access_key = "new1",
            secret_key = "new2"
        )
        client.update_s3cfg(s3cfg_id, updated_s3cfg)
        retrieved_s3cfg = client.get_s3cfg(s3cfg_id).response
        self.assertEqual('localhost:8001', retrieved_s3cfg['url'])
        # Delete s3cfg
        delete_response_status = client.delete_s3cfg(s3cfg_id).status_code
        self.assertEqual(204, delete_response_status)

    def test_invalid_s3cfg_schema(self):
        # This will fail schema validation
        with self.assertRaises(ValidationError):
            S3ConfigSchemaCreate(
                bad_param = "breaking bad"
            )

class IdentifierTest(unittest.TestCase):
    def list_identifiers(self):
        return client.list_identifiers()

    def test_create_update_delete_identifier(self):
        # Create identifier
        original_identifier = IdentifierTypeSchema(
            name = "demo_identifier",
            pattern = "*foo*"
        )
        created_identifier = client.create_identifier(original_identifier).response
        self.assertIsNotNone(created_identifier)
        self.assertIn('name', created_identifier)
        self.assertEqual('*foo*', created_identifier['pattern'])
        identifier_name = created_identifier['name']
        # Update identifier
        updated_identifier = IdentifierTypeSchema(
            name = "demo_identifier",
            pattern = "*new foo*"
        )
        client.update_identifier(updated_identifier)
        retrieved_identifier = client.get_identifier(identifier_name).response
        self.assertEqual('*new foo*', retrieved_identifier['pattern'])
        # Delete identifier
        delete_response_status = client.delete_identifier(identifier_name).status_code
        self.assertEqual(204, delete_response_status)

    def test_invalid_identifier_schema(self):
        with self.assertRaises(ValidationError):
            IdentifierTypeSchema(
                whoami = "an invalid value"
            )

class MediaTest(unittest.TestCase):
    def list_media(self):
        return client.list_media()

    def clean_pks(self, media):
        # Remove PKs for assertion
        for media_obj in media:
            del media_obj['pk']
            del media_obj['store_config']['pk']
        return media

    def test_bulk_create_read_search_delete_media(self):
        t = time.time()
        pids = [f'media_1_{t}', f'media_2_{t}']
        # Create multiple media objects
        media = [
            MediaSchemaCreate(
                pid = pids[0],
                pid_type = 'DEMO',
                store_config = dict(
                    type = 'DictStore',
                    bucket = 'testing_bucket',
                    s3_url = ''
                ),
                tags = ['test_tag']
            ),
            MediaSchemaCreate(
                pid = pids[1],
                pid_type = 'DEMO',
                store_config = dict(
                    type = 'DictStore',
                    bucket = 'testing_bucket',
                    s3_url = ''
                ),
                tags = ['test_tag']
            )
        ]
        created_media = client.create_bulk_media(media).response
        created_media = self.clean_pks(created_media)
        expected_media = [
            {
                'pid': pids[0],
                'pid_type': 'DEMO',
                'store_config': {
                    'type': 'DictStore',
                    'bucket': 'testing_bucket',
                    's3_url': ''
                },
                'store_status': 'PENDING',
                'identifiers': {},
                'metadata': {},
                'tags': ['test_tag']
            },
            {
                'pid': pids[1],
                'pid_type': 'DEMO',
                'store_config': {
                    'type': 'DictStore',
                    'bucket': 'testing_bucket',
                    's3_url': ''
                },
                'store_status': 'PENDING',
                'identifiers': {},
                'metadata': {},
                'tags': ['test_tag']
            }
        ]
        self.assertEqual(created_media, expected_media)
        # Find media objects by pid
        read_media = client.read_bulk_media(pids).response
        read_media = self.clean_pks(read_media)
        self.assertEqual(read_media, expected_media)
        # Find media objects by tags (TODO: add more vectors once implemented on the server)
        search_vectors = MediaSearchSchema(
            tags = ['test_tag']
        )
        searched_media = client.search_bulk_media(search_vectors).response
        searched_media = self.clean_pks(searched_media)
        self.assertEqual(searched_media, expected_media)
        # Remove media objects
        deleted_media = client.delete_bulk_media(pids).response
        expected_deleted_media = {
            'successes': pids,
            'failures': []
        }
        self.assertEqual(deleted_media, expected_deleted_media)

    # def test_update_patch_media_tags():
    #     pass

    # def test_update_media_storekeys_and_identifiers(self):
    #     pass

    # def test_update_patch_delete_media_metadata():
    #     pass


if __name__ == "__main__":

    # Run all tests
    unittest.main()

    # Run only one class of tests
    # suite = unittest.TestLoader().loadTestsFromTestCase(MediaTest)
    # unittest.TextTestRunner().run(suite)



    # REMOVE ALL MEDIA
    # media = client.list_media()
    # pidlist = []
    # for m in media:
    #     pid = m['pid']
    #     pidlist.append(pid)
    # client.delete_bulk_media(pidlist)
    # pprint(client.list_media())

    # S3CFG
    # [client.delete_s3cfg(pid) for pid in [51]]
    # pprint(client.list_s3cfgs().response)
