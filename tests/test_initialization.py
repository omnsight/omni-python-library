import unittest
import sys
from unittest.mock import MagicMock, patch

# Pre-mock to avoid side effects during import if any
sys.modules["openai"] = MagicMock()

# We can let redis and arango be real or mocked. 
# Since we want to test "class init (that code does not error out after invoking init)",
# we should ideally test the real classes if possible, OR test that they invoke the right things.
# Given the user wants to test "against class init", let's use mocks for the underlying drivers
# to avoid needing a running DB for *initialization* tests (fast feedback), 
# while the CRUD tests will use the docker container.

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.utils.singleton import Singleton

class TestInitialization(unittest.TestCase):
    def setUp(self):
        # Reset Singletons
        Singleton._instances = {}

    @patch("omni_python_library.clients.redis.redis.Redis")
    def test_redis_client_init(self, mock_redis):
        """Test RedisClient initialization."""
        client = RedisClient()
        client.init(host="localhost", port=6379, db=0, password="pass")
        
        self.assertEqual(client._host, "localhost")
        self.assertEqual(client._port, 6379)
        self.assertEqual(client._db, 0)
        self.assertEqual(client._password, "pass")
        
        mock_redis.assert_called_once_with(
            host="localhost", port=6379, db=0, password="pass", decode_responses=True
        )

    @patch("omni_python_library.clients.arangodb.ArangoClient")
    def test_arangodb_client_init(self, mock_arango_client_cls):
        """Test ArangoDBClient initialization."""
        mock_client_instance = MagicMock()
        mock_db = MagicMock()
        mock_arango_client_cls.return_value = mock_client_instance
        mock_client_instance.db.return_value = mock_db
        
        client = ArangoDBClient()
        client.init(host="http://localhost:8529", username="root", password="pw", db_name="test_db")
        
        self.assertEqual(client._host, "http://localhost:8529")
        self.assertEqual(client._username, "root")
        self.assertEqual(client._password, "pw")
        self.assertEqual(client._db_name, "test_db")
        
        mock_arango_client_cls.assert_called_once_with(hosts="http://localhost:8529")
        mock_client_instance.db.assert_called_once_with("test_db", username="root", password="pw")
        
        # Verify collection initialization
        # The init method calls _init_collection for several default collections
        self.assertTrue(mock_db.has_collection.called)

        # Verify view initialization
        self.assertTrue(mock_db.has_view.called)

    @patch("omni_python_library.dal.osint_data_factory.OpenAI")
    @patch("omni_python_library.dal.cacher.RedisClient")
    @patch("omni_python_library.clients.arangodb.ArangoDBClient")
    def test_dal_init(self, mock_arango, mock_redis, mock_openai):
        """Test OsintDataAccessLayer initialization."""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_instance.client = MagicMock()
        mock_redis.return_value = mock_redis_instance
        
        dal = OsintDataAccessLayer()
        dal.init(openai_api_key="sk-test", openai_base_url="http://api", llm_model="model-v1")
        
        self.assertEqual(dal._llm_model, "model-v1")
        
        # Verify OpenAI client creation
        mock_openai.assert_called_once_with(api_key="sk-test", base_url="http://api")

if __name__ == "__main__":
    unittest.main()
