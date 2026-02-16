import unittest

from arango import ArangoClient as PyArangoClient

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import EventMainData, OrganizationMainData, PersonMainData
from omni_python_library.utils.singleton import Singleton
from omni_python_library.utils.user import UserRole

# This test suite assumes a running ArangoDB and Redis instance (via docker-compose)
# We skip these tests if the services aren't available to avoid failing CI without docker.


def is_service_available():
    # Simple check - in a real scenario we might try to connect
    return True


class TestCRUD(unittest.TestCase):
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

    def test_person_crud(self):
        # Create
        person_data = PersonMainData(
            name="John Doe",
            role="Engineer",
            nationality="US",
            birth_date=100000,
            updated_at=200000,
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )

        created = self.dal.create_person(person_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.name, "John Doe")

        # Read
        fetched = self.dal.get_person(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "John Doe")
        self.assertEqual(fetched.role, "Engineer")

        # Update
        updated = self.dal.update_person(
            created.id, PersonMainData(role="Senior Engineer"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated.role, "Senior Engineer")

        # Read again (should hit cache or DB)
        fetched_updated = self.dal.get_person(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_updated.role, "Senior Engineer")

        # Delete
        deleted = self.dal.delete_entity(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertTrue(deleted)

        # Verify Delete
        fetched_deleted = self.dal.get_person(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(fetched_deleted)

    def test_organization_crud_with_pending(self):
        # Create
        org_data = OrganizationMainData(
            name="CyberCorp",
            type="Technology",
            founded_at=1609459200,  # Jan 1, 2021
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = self.dal.create_organization(org_data, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.name, "CyberCorp")

        # Update with in_pending=True
        self.dal.update_organization(
            created.id,
            OrganizationMainData(type="Global Technology"),
            owner="test_user_pending",
            roles=[UserRole.ADMIN],
            in_pending=True,
        )

        # Read with in_pending=False (default) - should get original data
        fetched_not_pending = self.dal.get_organization(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_not_pending.type, "Technology")

        # Read with in_pending=True - should get merged data
        fetched_pending = self.dal.get_organization(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertEqual(fetched_pending.type, "Global Technology")
        self.assertEqual(fetched_pending.name, "CyberCorp")  # Ensure other fields are intact

        # Perform a final update (in_pending=False)
        final_update = self.dal.update_organization(
            created.id, OrganizationMainData(founded_at=1609545600), owner="test_user_pending", roles=[UserRole.ADMIN]
        )  # Jan 2, 2021
        self.assertEqual(final_update.founded_at, 1609545600)
        self.assertEqual(final_update.type, "Global Technology")  # Check that pending change was applied

        # Read again, should be permanently updated
        fetched_final = self.dal.get_organization(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_final.founded_at, 1609545600)
        self.assertEqual(fetched_final.type, "Global Technology")

        # Clean up
        self.dal.delete_entity(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])

    def test_event_crud_with_pending_creation(self):
        # Create with in_pending=True
        event_data = EventMainData(
            title="Cyber Summit 2024",
            type="Conference",
            happened_at=1725148800,  # Sep 1, 2024
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = self.dal.create_event(
            event_data, owner="test_user_event", roles=[UserRole.ADMIN], in_pending=True
        )
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
