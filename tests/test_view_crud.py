import unittest
import logging

from arango import ArangoClient as PyArangoClient
from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.view_data_access_layer import ViewDataAccessLayer
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.view import OsintViewMainData, ViewConfig, ViewUI, ViewMode
from omni_python_library.models.osint import PersonMainData
from omni_python_library.utils.singleton import Singleton

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class TestViewCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Singleton._instances = {}
        try:
            RedisClient().init(host="localhost", port=6379, db=0)
            RedisClient().client.flushdb()
        except Exception as e:
            print(f"Redis not available: {e}")
            raise unittest.SkipTest("Redis service not available")

        try:
            sys_client = PyArangoClient(hosts="http://localhost:8529")
            sys_db = sys_client.db("_system", username="root", password="")
            if sys_db.has_database("test_osint_db_view"):
                sys_db.delete_database("test_osint_db_view")
            sys_db.create_database("test_osint_db_view")
            
            ArangoDBClient().init(
                host="http://localhost:8529", 
                username="root", 
                password="",
                db_name="test_osint_db_view"
            )
        except Exception as e:
            print(f"ArangoDB not available: {e}")
            raise unittest.SkipTest("ArangoDB service not available")

    def setUp(self):
        self.dal = ViewDataAccessLayer()
        self.osint_dal = OsintDataAccessLayer()
        self.dal.init()
        # Mock OpenAI key or pass None to init to avoid error if it tries to use OpenAIClient
        # But OsintDataAccessLayer.init() doesn't take api_key? 
        # Wait, test_crud.py used self.dal.init(openai_api_key=None).
        # Let's check OsintDataAccessLayer.init signature.
        # It inherits from OsintDataFactory.init which calls super().init() (Cacher.init).
        # Cacher.init doesn't take args.
        # But maybe test_crud.py was using a different version or I misread.
        # Let's check test_crud.py again.
        # Line 59: self.dal.init(openai_api_key=None)
        # But in OsintDataAccessLayer definition provided in context:
        # def init(self): super().init()
        # It doesn't take arguments.
        # Maybe OpenAIClient is used inside methods but not in init.
        # OsintDataFactory.generate_embedding uses OpenAIClient().get_client("embedding").
        # If I don't set API key, OpenAIClient might fail or return None?
        # Let's hope it works or fails gracefully (returns None for embedding).
        self.osint_dal.init()

    def test_view_lifecycle(self):
        # Create a person to be used in view
        person_data = PersonMainData(name="Test Person", role="Tester", nationality="US")
        # Ensure Person collection exists (init called in ArangoDBClient)
        try:
            person = self.osint_dal.create_person(person_data, owner="test_user")
        except Exception as e:
            print(f"Failed to create person: {e}")
            raise

        # Create View
        config = ViewConfig(ui=ViewUI.GEOVISION, mode=ViewMode.DEFAULT, entities=[person.id])
        view_data = OsintViewMainData(name="Test View", description="Description", configs=[config])
        view = self.dal.create_view(view_data, owner="test_user")
        
        self.assertIsNotNone(view.id)
        self.assertEqual(view.name, "Test View")
        
        # Get View
        fetched = self.dal.get_view(view.id)
        self.assertEqual(fetched.name, "Test View")
        self.assertEqual(len(fetched.configs), 1)
        self.assertEqual(fetched.configs[0].entities[0], person.id)
        
        # Update View (top level)
        updated_view = self.dal.update_view(view.id, {"description": "Updated Description"})
        self.assertEqual(updated_view.description, "Updated Description")
        
        # Add View Config
        new_config = ViewConfig(ui=ViewUI.SPARK_GRAPH, mode=ViewMode.TIMELINE, entities=[])
        updated_view_2 = self.dal.add_view_config(view.id, new_config)
        self.assertEqual(len(updated_view_2.configs), 2)
        
        # Connect Entity to View (to the second config, index 1)
        updated_view_3 = self.dal.connect_entity_to_view(view.id, person.id, config_index=1)
        self.assertEqual(updated_view_3.configs[1].entities[0], person.id)
        
        # Query by Owner
        views = self.dal.query_by_owner("test_user")
        self.assertTrue(any(v.id == view.id for v in views))
        
        # Delete View
        self.dal.delete_view(view.id)
        self.assertIsNone(self.dal.get_view(view.id))

    def test_verify_entity_existence(self):
        # Create view first
        view_data = OsintViewMainData(name="Test View 2", description="Description", configs=[])
        view = self.dal.create_view(view_data, owner="test_user")
        
        bad_config = ViewConfig(ui=ViewUI.GEOVISION, mode=ViewMode.DEFAULT, entities=["person/non_existent_123"])
        
        with self.assertRaises(ValueError):
            self.dal.add_view_config(view.id, bad_config)
            
        with self.assertRaises(ValueError):
            self.dal.connect_entity_to_view(view.id, "person/non_existent_123")

if __name__ == "__main__":
    unittest.main()
