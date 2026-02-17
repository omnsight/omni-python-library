import unittest

from arango import ArangoClient as PyArangoClient

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import SourceMainData
from omni_python_library.utils import PermissionDeniedError
from omni_python_library.utils.singleton import Singleton
from omni_python_library.utils.user import UserRole


class TestSourceCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Singleton._instances = {}
        RedisClient().init(host="localhost", port=6379)
        RedisClient().client.flushdb()

        sys_client = PyArangoClient(hosts="http://localhost:8529")
        sys_db = sys_client.db("_system", username="root", password="password")

        if sys_db.has_database("test_osint_db"):
            sys_db.delete_database("test_osint_db")

        sys_db.create_database("test_osint_db")

        ArangoDBClient().init(
            host="http://localhost:8529", username="root", password="password", db_name="test_osint_db"
        )

    def setUp(self):
        self.dal = OsintDataAccessLayer()
        from omni_python_library.clients.openai import OpenAIClient

        OpenAIClient().init()
        self.dal.init()

    def test_source_crud(self):
        # Create
        source_data = SourceMainData(
            url="http://example.com/source",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )

        created = self.dal.create_source(source_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.url, "http://example.com/source")

        # Read
        fetched = self.dal.get_source(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.url, "http://example.com/source")

        # Update
        updated = self.dal.update_source(
            created.id, SourceMainData(url="http://example.org/source"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated.url, "http://example.org/source")

        # Read again
        fetched_updated = self.dal.get_source(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_updated.url, "http://example.org/source")

        # Delete
        deleted = self.dal.delete_entity(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertTrue(deleted)

        # Verify Delete
        fetched_deleted = self.dal.get_source(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(fetched_deleted)

    def test_source_crud_with_pending(self):
        # Create
        source_data = SourceMainData(
            url="http://pending.com/source",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = self.dal.create_source(source_data, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.url, "http://pending.com/source")

        # Update with in_pending=True
        self.dal.update_source(
            created.id,
            SourceMainData(url="http://pending.org/source"),
            owner="test_user_pending",
            roles=[UserRole.ADMIN],
            in_pending=True,
        )

        # Read with in_pending=False (default) - should get original data
        fetched_not_pending = self.dal.get_source(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_not_pending.url, "http://pending.com/source")

        # Read with in_pending=True - should get merged data
        fetched_pending = self.dal.get_source(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertEqual(fetched_pending.url, "http://pending.org/source")

        # Perform a final update (in_pending=False)
        final_update = self.dal.update_source(
            created.id, SourceMainData(url="http://final.com/source"), owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(final_update.url, "http://final.com/source")

        # Read again, should be permanently updated
        fetched_final = self.dal.get_source(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_final.url, "http://final.com/source")

        # Clean up
        self.dal.delete_entity(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])

    def test_source_crud_permission_denied(self):
        # Create a source with a specific owner and roles
        source_data = SourceMainData(
            url="http://secure.com/source",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = self.dal.create_source(source_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)

        # Test creating with insufficient permissions
        with self.assertRaises(PermissionDeniedError):
            self.dal.create_source(source_data, owner="non_admin_user", roles=[UserRole.USER])

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            self.dal.get_source(created.id, owner="another_user", roles=[UserRole.USER])

        # Test updating with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            self.dal.update_source(
                created.id,
                SourceMainData(url="http://secure-updated.com/source"),
                owner="another_user",
                roles=[UserRole.USER],
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            self.dal.delete_entity(created.id, owner="another_user", roles=[UserRole.ADMIN])

        # Clean up
        self.dal.delete_entity(created.id, owner="owner_user", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
