import unittest

from omni_python_library import init_omni_library
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import SourceMainData
from omni_python_library.utils.config import UserRole
from omni_python_library.utils.errors import PermissionDeniedError


class TestSourceCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def test_source_crud(self):
        # Create
        source_data = SourceMainData(
            url="http://example.com/source",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )

        created = OsintDataAccessLayer().create_source(source_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.url, "http://example.com/source")

        # Read
        fetched = OsintDataAccessLayer().get_source(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.url, "http://example.com/source")

        # Update
        updated = OsintDataAccessLayer().update_source(
            created.id, SourceMainData(url="http://example.org/source"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated.url, "http://example.org/source")

        # Read again
        fetched_updated = OsintDataAccessLayer().get_source(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_updated.url, "http://example.org/source")

        # Delete
        deleted = OsintDataAccessLayer().delete_entity(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertTrue(deleted)

        # Verify Delete
        fetched_deleted = OsintDataAccessLayer().get_source(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(fetched_deleted)

    def test_source_crud_with_pending(self):
        # Create
        source_data = SourceMainData(
            url="http://pending.com/source",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_source(source_data, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.url, "http://pending.com/source")

        # Update with in_pending=True
        OsintDataAccessLayer().update_source(
            created.id,
            SourceMainData(url="http://pending.org/source"),
            owner="test_user_pending",
            roles=[UserRole.ADMIN],
            in_pending=True,
        )

        # Read with in_pending=False (default) - should get original data
        fetched_not_pending = OsintDataAccessLayer().get_source(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(fetched_not_pending.url, "http://pending.com/source")

        # Read with in_pending=True - should get merged data
        fetched_pending = OsintDataAccessLayer().get_source(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertEqual(fetched_pending.url, "http://pending.org/source")

        # Perform a final update (in_pending=False)
        final_update = OsintDataAccessLayer().update_source(
            created.id, SourceMainData(url="http://final.com/source"), owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(final_update.url, "http://final.com/source")

        # Read again, should be permanently updated
        fetched_final = OsintDataAccessLayer().get_source(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_final.url, "http://final.com/source")

        # Clean up
        OsintDataAccessLayer().delete_entity(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])

    def test_source_crud_permission_denied(self):
        # Create a source with a specific owner and roles
        source_data = SourceMainData(
            url="http://secure.com/source",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_source(source_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)

        # Test creating with insufficient permissions
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().create_source(source_data, owner="non_admin_user", roles=[UserRole.USER])

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().get_source(created.id, owner="another_user", roles=[UserRole.USER])

        # Test updating with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().update_source(
                created.id,
                SourceMainData(url="http://secure-updated.com/source"),
                owner="another_user",
                roles=[UserRole.USER],
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().delete_entity(created.id, owner="another_user", roles=[UserRole.ADMIN])

        # Clean up
        OsintDataAccessLayer().delete_entity(created.id, owner="owner_user", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
