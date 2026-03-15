import time
import unittest

from omni_python_library import init_omni_library
from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.monitoring_source_data_access_layer import MonitoringSourceDataAccessLayer
from omni_python_library.dal.view_data_access_layer import ViewDataAccessLayer
from omni_python_library.models import MonitoringSourceMainData, OsintViewMainData, SourceType
from omni_python_library.utils.config import UserRole
from omni_python_library.utils.errors import PermissionDeniedError


class TestMonitoringSourceDAL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def setUp(self):
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
                MonitoringSourceDataAccessLayer().delete_monitoring_source(ms_id, owner=owner)
            except:
                pass

    def test_crud_operations(self):
        # 1. Create
        ms = MonitoringSourceDataAccessLayer().create_monitoring_source(
            self.ms_data, owner=self.user_id, roles=[UserRole.ADMIN]
        )
        self.assertIsNotNone(ms.id)
        self.assertEqual(ms.name, self.ms_data.name)
        self.assertEqual(ms.owner, self.user_id)
        self.created_ids.append((ms.id, self.user_id))

        # 2. Get (Read)
        fetched_ms = MonitoringSourceDataAccessLayer().get_monitoring_source(ms.id, owner=self.user_id)
        self.assertIsNotNone(fetched_ms)
        self.assertEqual(fetched_ms.id, ms.id)
        self.assertEqual(fetched_ms.name, ms.name)

        # 3. Update
        update_data = MonitoringSourceMainData(name="Updated Test Source", reliability=90.0)
        updated_ms = MonitoringSourceDataAccessLayer().update_monitoring_source(
            ms.id, update_data, owner=self.user_id, roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated_ms.name, "Updated Test Source")
        self.assertEqual(updated_ms.reliability, 90.0)

        # Verify update with get
        fetched_updated_ms = MonitoringSourceDataAccessLayer().get_monitoring_source(ms.id, owner=self.user_id)
        self.assertEqual(fetched_updated_ms.name, "Updated Test Source")

        # 4. Get by User
        user_sources = MonitoringSourceDataAccessLayer().get_monitoring_sources_by_user(self.user_id)
        self.assertTrue(any(s.id == ms.id for s in user_sources))

        # 5. Delete
        MonitoringSourceDataAccessLayer().delete_monitoring_source(ms.id, owner=self.user_id)
        deleted_ms = MonitoringSourceDataAccessLayer().get_monitoring_source(ms.id, owner=self.user_id)
        self.assertIsNone(deleted_ms)
        self.created_ids.remove((ms.id, self.user_id))

    def test_view_connection(self):
        # Create MS
        ms = MonitoringSourceDataAccessLayer().create_monitoring_source(
            self.ms_data, owner=self.user_id, roles=[UserRole.ADMIN]
        )
        self.created_ids.append((ms.id, self.user_id))

        # Create View
        view_data = OsintViewMainData(name="Test View for MS")
        view = ViewDataAccessLayer().create_view(view_data, owner=self.user_id, roles=[UserRole.ADMIN])

        # Connect MS to View
        MonitoringSourceDataAccessLayer().connect_monitoring_source_to_view(
            view.id, ms.id, owner=self.user_id, roles=[UserRole.ADMIN]
        )

        # Get Views for MS
        views = MonitoringSourceDataAccessLayer().get_views(ms.id, owner=self.user_id)
        self.assertEqual(len(views), 1)
        self.assertEqual(views[0].id, view.id)

        # Clean up view (optional but good practice)
        ViewDataAccessLayer().delete_view(view.id, owner=self.user_id, roles=[UserRole.ADMIN])

    def test_query_monitoring_sources(self):
        # Create MS
        ms = MonitoringSourceDataAccessLayer().create_monitoring_source(
            self.ms_data, owner=self.user_id, roles=[UserRole.ADMIN]
        )
        self.created_ids.append((ms.id, self.user_id))

        # Wait for index to update (ArangoSearch is eventually consistent)
        time.sleep(2)

        # Query
        results = MonitoringSourceDataAccessLayer().query_monitoring_sources("Test", owner=self.user_id)
        self.assertIsInstance(results, list)
        if len(results) > 0:
            self.assertEqual(results[0].id, ms.id)

    def test_query_monitoring_sources_with_offset(self):
        # Create 2 MS
        ms1 = MonitoringSourceDataAccessLayer().create_monitoring_source(
            self.ms_data, owner=self.user_id, roles=[UserRole.ADMIN]
        )
        self.created_ids.append((ms1.id, self.user_id))
        ms2_data = self.ms_data.model_copy()
        ms2_data.name = "Test Source DAL 2"
        ms2 = MonitoringSourceDataAccessLayer().create_monitoring_source(
            ms2_data, owner=self.user_id, roles=[UserRole.ADMIN]
        )
        self.created_ids.append((ms2.id, self.user_id))

        # Wait for index to update (ArangoSearch is eventually consistent)
        time.sleep(2)

        # Query with limit 1 and offset 1
        results = MonitoringSourceDataAccessLayer().query_monitoring_sources(
            "Test", owner=self.user_id, limit=1, offset=1
        )
        self.assertEqual(len(results), 1)

        # Query with limit 2
        all_results = MonitoringSourceDataAccessLayer().query_monitoring_sources("Test", owner=self.user_id, limit=2)
        self.assertEqual(len(all_results), 2)

        # The single result with offset should be one of the two results
        self.assertIn(results[0].id, [r.id for r in all_results])

        # And it should not be the first one
        self.assertNotEqual(results[0].id, all_results[0].id)

    def test_monitoring_source_permission_denied(self):
        # Create a source with a specific owner
        ms = MonitoringSourceDataAccessLayer().create_monitoring_source(
            self.ms_data, owner="owner_user", roles=[UserRole.ADMIN]
        )
        self.created_ids.append((ms.id, "owner_user"))

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            MonitoringSourceDataAccessLayer().get_monitoring_source(ms.id, owner="another_user")

        # Test updating with wrong owner
        with self.assertRaises(PermissionDeniedError):
            MonitoringSourceDataAccessLayer().update_monitoring_source(
                ms.id, MonitoringSourceMainData(name="Illegal Update"), owner="another_user", roles=[]
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            MonitoringSourceDataAccessLayer().delete_monitoring_source(ms.id, owner="another_user")

        # Test getting by user with a different user
        user_sources = MonitoringSourceDataAccessLayer().get_monitoring_sources_by_user("another_user")
        self.assertFalse(any(s.id == ms.id for s in user_sources))


if __name__ == "__main__":
    unittest.main()
