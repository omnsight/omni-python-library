import unittest

from omni_python_library import init_omni_library
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import EventMainData
from omni_python_library.utils import PermissionDeniedError
from omni_python_library.utils.user import UserRole


class TestEventCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def test_event_crud(self):
        # Create
        event_data = EventMainData(
            title="Tech Meetup",
            type="Meetup",
            happened_at=1725148800,  # Sep 1, 2024
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_event(event_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.title, "Tech Meetup")

        # Read
        fetched = OsintDataAccessLayer().get_event(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Tech Meetup")
        self.assertEqual(fetched.type, "Meetup")

        # Update
        updated = OsintDataAccessLayer().update_event(
            created.id, EventMainData(type="Community Meetup"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated.type, "Community Meetup")

        # Read again
        fetched_updated = OsintDataAccessLayer().get_event(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_updated.type, "Community Meetup")

        # Delete
        deleted = OsintDataAccessLayer().delete_entity(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertTrue(deleted)

        # Verify Delete
        fetched_deleted = OsintDataAccessLayer().get_event(created.id, owner="test_user", roles=[UserRole.ADMIN])
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
        created = OsintDataAccessLayer().create_event(
            event_data, owner="test_user_event", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertIsNotNone(created)
        self.assertEqual(created.title, "Cyber Summit 2024")

        # Read with in_pending=False - should get the minimal document
        fetched_not_pending = OsintDataAccessLayer().get_event(
            created.id, owner="test_user_event", roles=[UserRole.ADMIN]
        )
        self.assertIsNotNone(fetched_not_pending)
        self.assertEqual(fetched_not_pending.title, "Cyber Summit 2024")
        self.assertIsNone(fetched_not_pending.type)  # Verify that pending data is not present

        # Read with in_pending=True - should find it
        fetched_pending = OsintDataAccessLayer().get_event(
            created.id, owner="test_user_event", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertIsNotNone(fetched_pending)
        self.assertEqual(fetched_pending.title, "Cyber Summit 2024")

        # Perform an update to commit the pending creation
        final_update = OsintDataAccessLayer().update_event(
            created.id, EventMainData(type="Tech Conference"), owner="test_user_event", roles=[UserRole.ADMIN]
        )
        self.assertEqual(final_update.type, "Tech Conference")

        # Read again, should be permanently updated and accessible
        fetched_final = OsintDataAccessLayer().get_event(created.id, owner="test_user_event", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched_final)
        self.assertEqual(fetched_final.type, "Tech Conference")

        # Clean up
        OsintDataAccessLayer().delete_entity(created.id, owner="test_user_event", roles=[UserRole.ADMIN])

    def test_event_crud_permission_denied(self):
        # Create an event with a specific owner and roles
        event_data = EventMainData(
            title="Top Secret Meeting",
            type="Meeting",
            happened_at=1725148800,
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_event(event_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)

        # Test creating with insufficient permissions
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().create_event(event_data, owner="non_admin_user", roles=[UserRole.USER])

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().get_event(created.id, owner="another_user", roles=[UserRole.USER])

        # Test updating with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().update_event(
                created.id, EventMainData(type="Super Secret Meeting"), owner="another_user", roles=[UserRole.USER]
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().delete_entity(created.id, owner="another_user", roles=[UserRole.ADMIN])

        # Clean up
        OsintDataAccessLayer().delete_entity(created.id, owner="owner_user", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
