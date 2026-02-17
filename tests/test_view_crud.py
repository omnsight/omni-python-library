import logging
import unittest

from arango import ArangoClient as PyArangoClient

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view_data_access_layer import ViewDataAccessLayer
from omni_python_library.models.osint import PersonMainData
from omni_python_library.models.view import OsintViewMainData, ViewConfig, ViewMode, ViewUI
from omni_python_library.utils import NotFoundError, PermissionDeniedError
from omni_python_library.utils.singleton import Singleton
from omni_python_library.utils.user import UserRole

# Configure logging
logging.basicConfig(level=logging.DEBUG)


class TestViewCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        self.dal = ViewDataAccessLayer()
        self.osint_dal = OsintDataAccessLayer()
        # Ensure OpenAIClient is initialized
        from omni_python_library.clients.openai import OpenAIClient

        OpenAIClient().init()
        self.dal.init()
        self.osint_dal.init()

    def test_view_lifecycle(self):
        # Create a person to be used in view
        person_data = PersonMainData(name="Test Person", role="Tester", nationality="US")
        # Ensure Person collection exists (init called in ArangoDBClient)
        try:
            person = self.osint_dal.create_person(person_data, owner="test_user", roles=[UserRole.ADMIN])
        except Exception as e:
            print(f"Failed to create person: {e}")
            raise

        # Create View
        config = ViewConfig(ui=ViewUI.GEOVISION, mode=ViewMode.DEFAULT, entities=[person.id])
        view_data = OsintViewMainData(name="Test View", description="Description", configs=[config])
        view = self.dal.create_view(view_data, owner="test_user", roles=[UserRole.ADMIN])

        self.assertIsNotNone(view.id)
        self.assertEqual(view.name, "Test View")

        # Get View
        fetched = self.dal.get_view(view.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched.name, "Test View")
        self.assertEqual(len(fetched.configs), 1)
        self.assertEqual(fetched.configs[0].entities[0], person.id)

        # Update View (top level)
        updated_view = self.dal.update_view(
            view.id, OsintViewMainData(description="Updated Description"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated_view.description, "Updated Description")

        # Add View Config
        new_config = ViewConfig(ui=ViewUI.SPARK_GRAPH, mode=ViewMode.TIMELINE, entities=[])
        updated_view_2 = self.dal.add_view_config(view.id, new_config, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(len(updated_view_2.configs), 2)

        # Connect Entity to View (to the second config, index 1)
        self.dal.connect_entity_to_view(view.id, person.id, owner="test_user", roles=[UserRole.ADMIN])
        entities = self.dal.get_entities(view.id, owner="test_user", roles=[UserRole.ADMIN])
        assert any(entity.id == person.id for entity in entities)

        # Query by Text
        views = self.dal.query_views("Test View", "test_user")
        self.assertTrue(any(v.id == view.id for v in views))

        # Query by Description
        views = self.dal.query_views("Updated Description", "test_user")
        self.assertTrue(any(v.id == view.id for v in views))

        # Delete View
        self.dal.delete_view(view.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(self.dal.get_view(view.id, owner="test_user", roles=[UserRole.ADMIN]))

    def test_verify_entity_existence(self):
        # Create view first
        view_data = OsintViewMainData(name="Test View 2", description="Description", configs=[])
        view = self.dal.create_view(view_data, owner="test_user", roles=[UserRole.ADMIN])

        bad_config = ViewConfig(ui=ViewUI.GEOVISION, mode=ViewMode.DEFAULT, entities=["person/non_existent_123"])

        with self.assertRaises(NotFoundError):
            self.dal.add_view_config(view.id, bad_config, owner="test_user", roles=[UserRole.ADMIN])

        with self.assertRaises(NotFoundError):
            self.dal.connect_entity_to_view(
                view.id, "person/non_existent_123", owner="test_user", roles=[UserRole.ADMIN]
            )

    def test_view_crud_permission_denied(self):
        # Create a view with a specific owner and roles
        view_data = OsintViewMainData(
            name="Protected View",
            description="A view with restricted access",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = self.dal.create_view(view_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)

        # Test creating with insufficient permissions
        with self.assertRaises(PermissionDeniedError):
            self.dal.create_view(view_data, owner="non_admin_user", roles=[UserRole.USER])

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            self.dal.get_view(created.id, owner="another_user", roles=[UserRole.USER])

        # Test updating with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            self.dal.update_view(
                created.id,
                OsintViewMainData(description="Updated by wrong user"),
                owner="another_user",
                roles=[UserRole.USER],
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            self.dal.delete_view(created.id, owner="another_user", roles=[UserRole.ADMIN])

        # Clean up
        self.dal.delete_view(created.id, owner="owner_user", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
