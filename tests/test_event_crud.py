import unittest

from arango import ArangoClient as PyArangoClient

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import EventMainData
from omni_python_library.utils.singleton import Singleton
from omni_python_library.utils.user import UserRole


class TestEventCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure clients to point to Docker services
        # Assuming defaults from docker-compose
        Singleton._instances = {}

        RedisClient().init(host="localhost", port=6379)
        # Clear Redis
        RedisClient().client.flushdb()

        # Create DB if not exists using direct client to avoid initializing collections in _system
        sys_client = PyArangoClient(hosts="http://localhost:8529")
        sys_db = sys_client.db("_system", username="root", password="password")

        # Drop existing DB to ensure clean state
        if sys_db.has_database("test_osint_db"):
            sys_db.delete_database("test_osint_db")

        sys_db.create_database("test_osint_db")

        # Now initialize the application client
        ArangoDBClient().init(
            host="http://localhost:8529", username="root", password="password", db_name="test_osint_db"
        )

    def setUp(self):
        # Reset DAL for each test
        self.dal = OsintDataAccessLayer()
        # Ensure OpenAIClient is initialized (even if empty) to avoid AttributeError
        from omni_python_library.clients.openai import OpenAIClient

        OpenAIClient().init()
        self.dal.init()

    def test_event_crud(self):
        # Create
        event_data = EventMainData(
            title="Tech Meetup",
            type="Meetup",
            happened_at=1725148800,  # Sep 1, 2024
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = self.dal.create_event(event_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.title, "Tech Meetup")

        # Read
        fetched = self.dal.get_event(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Tech Meetup")
        self.assertEqual(fetched.type, "Meetup")

        # Update
        updated = self.dal.update_event(
            created.id, EventMainData(type="Community Meetup"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated.type, "Community Meetup")

        # Read again
        fetched_updated = self.dal.get_event(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_updated.type, "Community Meetup")

        # Delete
        deleted = self.dal.delete_entity(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertTrue(deleted)

        # Verify Delete
        fetched_deleted = self.dal.get_event(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(fetched_deleted)

    def test_event_crud_with_pending_creation(self):
        # Create with in_pending=True
        event_data = EventMainData(
            title="Cyber Summit 2024",
            type="Conference",
            happened_at=1725148800,  # Sep 1, 2024
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = self.dal.create_event(event_data, owner="test_user_event", roles=[UserRole.ADMIN], in_pending=True)
        self.assertIsNotNone(created)
        self.assertEqual(created.title, "Cyber Summit 2024")

        # Read with in_pending=False - should get the minimal document
        fetched_not_pending = self.dal.get_event(created.id, owner="test_user_event", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched_not_pending)
        self.assertEqual(fetched_not_pending.title, "Cyber Summit 2024")
        self.assertIsNone(fetched_not_pending.type)  # Verify that pending data is not present

        # Read with in_pending=True - should find it
        fetched_pending = self.dal.get_event(
            created.id, owner="test_user_event", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertIsNotNone(fetched_pending)
        self.assertEqual(fetched_pending.title, "Cyber Summit 2024")

        # Perform an update to commit the pending creation
        final_update = self.dal.update_event(
            created.id, EventMainData(type="Tech Conference"), owner="test_user_event", roles=[UserRole.ADMIN]
        )
        self.assertEqual(final_update.type, "Tech Conference")

        # Read again, should be permanently updated and accessible
        fetched_final = self.dal.get_event(created.id, owner="test_user_event", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched_final)
        self.assertEqual(fetched_final.type, "Tech Conference")

        # Clean up
        self.dal.delete_entity(created.id, owner="test_user_event", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
