import unittest

from arango import ArangoClient as PyArangoClient
from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.utils.singleton import Singleton
from omni_python_library.models.osint import Person

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
        
        try:
            RedisClient().init(host="localhost", port=6379, db=0)
            # Clear Redis
            RedisClient().client.flushdb()
        except Exception as e:
            print(f"Redis not available: {e}")
            raise unittest.SkipTest("Redis service not available. Skipping integration tests.")
            
        try:
            # Create DB if not exists using direct client to avoid initializing collections in _system
            sys_client = PyArangoClient(hosts="http://localhost:8529")
            sys_db = sys_client.db("_system", username="root", password="")
            
            # Drop existing DB to ensure clean state
            if sys_db.has_database("test_osint_db"):
                sys_db.delete_database("test_osint_db")
                
            sys_db.create_database("test_osint_db")
            
            # Now initialize the application client
            ArangoDBClient().init(
                host="http://localhost:8529", 
                username="root", 
                password="",
                db_name="test_osint_db"
            )
        except Exception as e:
            print(f"ArangoDB not available: {e}")
            raise unittest.SkipTest("ArangoDB service not available. Skipping integration tests.")

    def setUp(self):
        # Reset DAL for each test
        self.dal = OsintDataAccessLayer()
        # We don't need real OpenAI for CRUD unless we test embeddings, 
        # but the code requires api_key to init client. We can pass None to skip embedding generation.
        self.dal.init(openai_api_key=None)

    def test_person_crud(self):
        # Create
        person = Person(
            name="John Doe",
            role="Engineer",
            nationality="US",
            birth_date=100000,
            updated_at=200000,
            owner="test_user",
            _id="person/john_doe",
            _key="john_doe",
            _rev="1"
        )
        
        # We use a try-except block because if the DB isn't running, this will fail.
        # Ideally we'd skip, but let's try to run it.
        try:
            created = self.dal.create_person(person)
            self.assertIsNotNone(created)
            self.assertEqual(created.name, "John Doe")
            
            # Read
            fetched = self.dal.get_person(created.id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.name, "John Doe")
            self.assertEqual(fetched.role, "Engineer")
            
            # Update
            updated = self.dal.update_person(created.id, {"role": "Senior Engineer"})
            self.assertEqual(updated.role, "Senior Engineer")
            
            # Read again (should hit cache or DB)
            fetched_updated = self.dal.get_person(created.id)
            self.assertEqual(fetched_updated.role, "Senior Engineer")
            
            # Delete
            deleted = self.dal.delete_entity(created.id)
            self.assertTrue(deleted)
            
            # Verify Delete
            fetched_deleted = self.dal.get_person(created.id)
            self.assertIsNone(fetched_deleted)
    
        except Exception as e:
            # Fail if it's a code error, skip if connection error?
            # For this task, we assume the user will run docker-compose up
            raise e

if __name__ == "__main__":
    unittest.main()
