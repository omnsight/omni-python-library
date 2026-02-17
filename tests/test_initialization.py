import sys
import unittest
from unittest.mock import MagicMock, patch

from omni_python_library import init_omni_library
from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.utils.config_registry import LLMConstant
from omni_python_library.utils.singleton import Singleton

sys.modules["openai"] = MagicMock()


class TestInitialization(unittest.TestCase):
    def setUp(self):
        # Reset Singletons
        Singleton._instances = {}

    @patch("omni_python_library.clients.redis.Redis")
    def test_redis_client_init(self, mock_redis):
        """Test RedisClient initialization."""
        client = RedisClient()
        client.init(host="localhost", port=6379, password="pass")

        self.assertEqual(client._host, "localhost")
        self.assertEqual(client._port, 6379)
        self.assertEqual(client._password, "pass")

        self.assertEqual(mock_redis.call_count, 3)
        mock_redis.assert_any_call(host="localhost", port=6379, db=0, password="pass", decode_responses=True)
        mock_redis.assert_any_call(host="localhost", port=6379, db=1, password="pass", decode_responses=True)
        mock_redis.assert_any_call(host="localhost", port=6379, db=2, password="pass", decode_responses=True)

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

    @patch("omni_python_library.dal.base.cacher.RedisClient")
    @patch("omni_python_library.dal.osint_data_access_layer.ArangoDBClient")
    def test_dal_init(self, mock_arango, mock_redis):
        """Test OsintDataAccessLayer initialization."""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_instance.client = MagicMock()
        mock_redis.return_value = mock_redis_instance

        # Setup ArangoDBClient mock instance
        mock_arango_instance = MagicMock()
        mock_arango.return_value = mock_arango_instance
        # init calls init_collection which calls _db.has_collection, so we need _db mock
        mock_arango_instance._db = MagicMock()

        dal = OsintDataAccessLayer()
        dal.init()

    @patch("omni_python_library.MonitorTriggerDataAccessLayer")
    @patch("omni_python_library.MonitoringSourceDataAccessLayer")
    @patch("omni_python_library.ViewDataAccessLayer")
    @patch("omni_python_library.OsintDataAccessLayer")
    @patch("omni_python_library.OpenAIClient")
    @patch("omni_python_library.RedisClient")
    @patch("omni_python_library.ArangoDBClient")
    @patch("omni_python_library.ConfigRegistry")
    def test_init_omni_library(
        self,
        mock_config_registry,
        mock_arango_client,
        mock_redis_client,
        mock_openai_client,
        mock_osint_dal,
        mock_view_dal,
        mock_monitoring_source_dal,
        mock_monitor_trigger_dal,
    ):
        """Test the main library initialization function."""
        # Setup mock for ConfigRegistry
        mock_config_instance = MagicMock()
        mock_config_registry.return_value = mock_config_instance
        config_values = {
            "ARANGODB_HOST": "arango_host",
            "ARANGODB_USERNAME": "arango_user",
            "ARANGODB_PASSWORD": "arango_pass",
            "ARANGODB_DB_NAME": "arango_db",
            "ARANGODB_EMBEDDING_DIMENSION": "1536",
            "REDIS_HOST": "redis_host",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "REDIS_PASSWORD": "redis_pass",
            "EMBEDDING_AI_API_KEY": "openai_key",
            "EMBEDDING_MODEL": "openai_model",
        }
        mock_config_instance.get.side_effect = lambda key: config_values[key]

        # Setup mocks for clients
        mock_arango_instance = MagicMock()
        mock_arango_client.return_value = mock_arango_instance

        mock_redis_instance = MagicMock()
        mock_redis_client.return_value = mock_redis_instance

        mock_openai_instance = MagicMock()
        mock_openai_client.return_value = mock_openai_instance

        # Setup mocks for DALs
        mock_osint_instance = MagicMock()
        mock_osint_dal.return_value = mock_osint_instance

        mock_view_instance = MagicMock()
        mock_view_dal.return_value = mock_view_instance

        mock_monitoring_source_instance = MagicMock()
        mock_monitoring_source_dal.return_value = mock_monitoring_source_instance

        # Call the function
        init_omni_library()

        # Assertions
        mock_arango_instance.init.assert_called_once_with(
            host="arango_host",
            username="arango_user",
            password="arango_pass",
            db_name="arango_db",
            embedding_dimension=1536,
        )
        mock_redis_instance.init.assert_called_once_with(
            host="redis_host",
            port=6379,
            db=0,
            password="redis_pass",
        )
        mock_openai_instance.init.assert_called_once()
        mock_openai_instance.add_client.assert_called_once_with(
            model_use=LLMConstant.EMBEDDING,
            api_key="openai_key",
            model="openai_model",
        )
        mock_osint_instance.init.assert_called_once()
        mock_view_instance.init.assert_called_once()
        mock_monitoring_source_instance.init.assert_called_once()
        mock_monitor_trigger_dal.assert_called_once()


if __name__ == "__main__":
    unittest.main()
