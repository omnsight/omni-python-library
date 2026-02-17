import time
import unittest

from arango import ArangoClient as PyArangoClient

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.monitoring_source_data_access_layer import MonitoringSourceDataAccessLayer
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view_data_access_layer import ViewDataAccessLayer
from omni_python_library.models import MonitoringSourceMainData, OsintViewMainData, SourceType
from omni_python_library.utils import PermissionDeniedError
from omni_python_library.utils.singleton import Singleton
from omni_python_library.utils.user import UserRole


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
        for ms_id, owner in self.created_ids:
            try:
                self.dal.delete_monitoring_source(ms_id, owner=owner)
            except:
                pass

    def test_crud_operations(self):
        # 1. Create
        ms = self.dal.create_monitoring_source(self.ms_data, owner=self.user_id, roles=[UserRole.ADMIN])
        self.assertIsNotNone(ms.id)
        self.assertEqual(ms.name, self.ms_data.name)
        self.assertEqual(ms.owner, self.user_id)
        self.created_ids.append((ms.id, self.user_id))

        # 2. Get (Read)
        fetched_ms = self.dal.get_monitoring_source(ms.id, owner=self.user_id)
        self.assertIsNotNone(fetched_ms)
        self.assertEqual(fetched_ms.id, ms.id)
        self.assertEqual(fetched_ms.name, ms.name)

        # 3. Update
        update_data = MonitoringSourceMainData(name="Updated Test Source", reliability=90.0)
        updated_ms = self.dal.update_monitoring_source(ms.id, update_data, owner=self.user_id, roles=[UserRole.ADMIN])
        self.assertEqual(updated_ms.name, "Updated Test Source")
        self.assertEqual(updated_ms.reliability, 90.0)

        # Verify update with get
        fetched_updated_ms = self.dal.get_monitoring_source(ms.id, owner=self.user_id)
        self.assertEqual(fetched_updated_ms.name, "Updated Test Source")

        # 4. Get by User
        user_sources = self.dal.get_monitoring_sources_by_user(self.user_id)
        self.assertTrue(any(s.id == ms.id for s in user_sources))

        # 5. Delete
        self.dal.delete_monitoring_source(ms.id, owner=self.user_id)
        deleted_ms = self.dal.get_monitoring_source(ms.id, owner=self.user_id)
        self.assertIsNone(deleted_ms)
        self.created_ids.remove((ms.id, self.user_id))

    def test_view_connection(self):
        # Create MS
        ms = self.dal.create_monitoring_source(self.ms_data, owner=self.user_id, roles=[UserRole.ADMIN])
        self.created_ids.append((ms.id, self.user_id))

        # Create View
        view_data = OsintViewMainData(name="Test View for MS")
        view = self.view_dal.create_view(view_data, owner=self.user_id, roles=[UserRole.ADMIN])

        # Connect MS to View
        self.dal.connect_monitoring_source_to_view(view.id, ms.id, owner=self.user_id, roles=[UserRole.ADMIN])

        # Get Views for MS
        query = f"""
            FOR v IN 1..1 OUTBOUND @view_id GRAPH 'osint_view_graph'
                FILTER v._id == @ms_id
                FILTER v.owner == @owner
                RETURN v
        """
        bind_vars = {"view_id": view.id, "ms_id": ms.id, "owner": self.user_id}
        # Note: This is a direct query, so it bypasses DAL-level auth.
        # The connection itself is what we are testing.
        cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["_id"], ms.id)

        # Clean up view (optional but good practice)
        self.view_dal.delete_view(view.id, owner=self.user_id, roles=[UserRole.ADMIN])

    def test_query_monitoring_sources(self):
        # Create MS
        ms = self.dal.create_monitoring_source(self.ms_data, owner=self.user_id, roles=[UserRole.ADMIN])
        self.created_ids.append((ms.id, self.user_id))

        # Wait for index to update (ArangoSearch is eventually consistent)
        time.sleep(2)

        # Query
        results = self.dal.query_monitoring_sources("Test", owner=self.user_id)
        self.assertIsInstance(results, list)
        if len(results) > 0:
            self.assertEqual(results[0].id, ms.id)

    def test_monitoring_source_permission_denied(self):
        # Create a source with a specific owner
        ms = self.dal.create_monitoring_source(self.ms_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.created_ids.append((ms.id, "owner_user"))

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            self.dal.get_monitoring_source(ms.id, owner="another_user")

        # Test updating with wrong owner
        with self.assertRaises(PermissionDeniedError):
            self.dal.update_monitoring_source(
                ms.id, MonitoringSourceMainData(name="Illegal Update"), owner="another_user", roles=[]
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            self.dal.delete_monitoring_source(ms.id, owner="another_user")

        # Test getting by user with a different user
        user_sources = self.dal.get_monitoring_sources_by_user("another_user")
        self.assertFalse(any(s.id == ms.id for s in user_sources))


if __name__ == "__main__":
    unittest.main()
