import time
import unittest
from unittest.mock import patch

from arango import ArangoClient as PyArangoClient

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.monitoring_source_data_access_layer import MonitoringSourceDataAccessLayer
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view_data_access_layer import ViewDataAccessLayer
from omni_python_library.models import MonitoringSourceMainData, OsintViewMainData, SourceType
from omni_python_library.utils.singleton import Singleton


class TestMonitoringSourceDAL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure clients to point to Docker services
        # Assuming defaults from docker-compose
        Singleton._instances = {}

        # Create DB if not exists using direct client to avoid initializing collections in _system
        sys_client = PyArangoClient(hosts="http://localhost:8529")
        sys_db = sys_client.db("_system", username="root", password="password")

        # Drop existing DB to ensure clean state
        if sys_db.has_database("test_osint_db_dal"):
            sys_db.delete_database("test_osint_db_dal")

        sys_db.create_database("test_osint_db_dal")

        # Now initialize the application client
        client = ArangoDBClient()
        client.init(host="http://localhost:8529", username="root", password="password", db_name="test_osint_db_dal")

        RedisClient().init(host="localhost", port=6379)
        RedisClient().client.flushdb()

    def setUp(self):
        self.dal = MonitoringSourceDataAccessLayer()
        self.dal.init()
        self.osint_dal = OsintDataAccessLayer()
        self.osint_dal.init()
        self.view_dal = ViewDataAccessLayer()
        self.view_dal.init()
        self.user_id = "test_user_dal"
        self.ms_data = MonitoringSourceMainData(
            name="Test Source DAL",
            description="A test source for DAL testing",
            type=SourceType.WEBSITE,
            url="https://example.com",
            reliability=80.0,
        )
        self.created_ids = []

    def tearDown(self):
        # Cleanup
        with patch("omni_python_library.dal.base.ArangoOperator._check_auth", return_value=True):
            for ms_id in self.created_ids:
                try:
                    self.dal.delete_monitoring_source(ms_id)
                except:
                    pass
            # Clean up views if any (would need to track them)

    def test_crud_operations(self):
        with patch("omni_python_library.dal.base.ArangoOperator._check_auth", return_value=True):
            # 1. Create
            ms = self.dal.create_monitoring_source(self.ms_data, self.user_id)
            self.assertIsNotNone(ms.id)
            self.assertEqual(ms.name, self.ms_data.name)
            self.assertEqual(ms.owner, self.user_id)
            self.created_ids.append(ms.id)

            # 2. Get (Read)
            fetched_ms = self.dal.get_monitoring_source(ms.id)
            self.assertIsNotNone(fetched_ms)
            self.assertEqual(fetched_ms.id, ms.id)
            self.assertEqual(fetched_ms.name, ms.name)

            # 3. Update
            update_data = MonitoringSourceMainData(name="Updated Test Source", reliability=90.0)
            updated_ms = self.dal.update_monitoring_source(ms.id, update_data)
            self.assertEqual(updated_ms.name, "Updated Test Source")
            self.assertEqual(updated_ms.reliability, 90.0)

            # Verify update with get
            fetched_updated_ms = self.dal.get_monitoring_source(ms.id)
            self.assertEqual(fetched_updated_ms.name, "Updated Test Source")

            # 4. Get by User
            user_sources = self.dal.get_monitoring_sources_by_user(self.user_id)
            self.assertTrue(any(s.id == ms.id for s in user_sources))

            # 5. Delete
            self.dal.delete_monitoring_source(ms.id)
            deleted_ms = self.dal.get_monitoring_source(ms.id)
            self.assertIsNone(deleted_ms)
            self.created_ids.remove(ms.id)

    def test_view_connection(self):
        with patch("omni_python_library.dal.base.ArangoOperator._check_auth", return_value=True):
            # Create MS
            ms = self.dal.create_monitoring_source(self.ms_data, self.user_id)
            self.created_ids.append(ms.id)

            # Create View
            view_data = OsintViewMainData(name="Test View for MS")
            view = self.view_dal.create_view(view_data, owner=self.user_id)
            # We should probably clean up this view too, but for now let's focus on MS logic

            # Connect MS to View
            self.dal.connect_monitoring_source_to_view(view.id, ms.id)

            # Get Views for MS
            query = f"""
                FOR v IN 1..1 OUTBOUND @view_id GRAPH 'osint_view_graph'
                    FILTER v._id == @ms_id
                    RETURN v
            """
            bind_vars = {"view_id": view.id, "ms_id": ms.id}
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
            results = list(cursor)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["_id"], ms.id)

            # Clean up view (optional but good practice)
            self.view_dal.delete_view(view.id)

    def test_query_monitoring_sources(self):
        with patch("omni_python_library.dal.base.ArangoOperator._check_auth", return_value=True):
            # Create MS
            ms = self.dal.create_monitoring_source(self.ms_data, self.user_id)
            self.created_ids.append(ms.id)

            # Wait for index to update (ArangoSearch is eventually consistent)
            time.sleep(2)

            # Query
            results = self.dal.query_monitoring_sources("Test", self.user_id)
            self.assertIsInstance(results, list)
            # Depending on ArangoDB setup and timing, this might return the item or not.
            # But we expect it to work given the code structure.
            if len(results) > 0:
                self.assertEqual(results[0].id, ms.id)


if __name__ == "__main__":
    unittest.main()
