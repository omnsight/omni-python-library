import unittest

from omni_python_library import init_omni_library
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import OrganizationMainData
from omni_python_library.utils import PermissionDeniedError
from omni_python_library.utils.user import UserRole


class TestOrganizationCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def test_organization_crud(self):
        # Create
        org_data = OrganizationMainData(
            name="TestCorp",
            type="Business",
            founded_at=1609459200,  # Jan 1, 2021
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_organization(org_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.name, "TestCorp")

        # Read
        fetched = OsintDataAccessLayer().get_organization(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "TestCorp")
        self.assertEqual(fetched.type, "Business")

        # Update
        updated = OsintDataAccessLayer().update_organization(
            created.id, OrganizationMainData(type="Global Business"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated.type, "Global Business")

        # Read again
        fetched_updated = OsintDataAccessLayer().get_organization(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_updated.type, "Global Business")

        # Delete
        deleted = OsintDataAccessLayer().delete_entity(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertTrue(deleted)

        # Verify Delete
        fetched_deleted = OsintDataAccessLayer().get_organization(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(fetched_deleted)

    def test_organization_crud_with_pending(self):
        # Create
        org_data = OrganizationMainData(
            name="CyberCorp",
            type="Technology",
            founded_at=1609459200,  # Jan 1, 2021
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_organization(
            org_data, owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertIsNotNone(created)
        self.assertEqual(created.name, "CyberCorp")

        # Update with in_pending=True
        OsintDataAccessLayer().update_organization(
            created.id,
            OrganizationMainData(type="Global Technology"),
            owner="test_user_pending",
            roles=[UserRole.ADMIN],
            in_pending=True,
        )

        # Read with in_pending=False (default) - should get original data
        fetched_not_pending = OsintDataAccessLayer().get_organization(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(fetched_not_pending.type, "Technology")

        # Read with in_pending=True - should get merged data
        fetched_pending = OsintDataAccessLayer().get_organization(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertEqual(fetched_pending.type, "Global Technology")
        self.assertEqual(fetched_pending.name, "CyberCorp")  # Ensure other fields are intact

        # Perform a final update (in_pending=False)
        final_update = OsintDataAccessLayer().update_organization(
            created.id, OrganizationMainData(founded_at=1609545600), owner="test_user_pending", roles=[UserRole.ADMIN]
        )  # Jan 2, 2021
        self.assertEqual(final_update.founded_at, 1609545600)
        self.assertEqual(final_update.type, "Global Technology")  # Check that pending change was applied

        # Read again, should be permanently updated
        fetched_final = OsintDataAccessLayer().get_organization(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(fetched_final.founded_at, 1609545600)
        self.assertEqual(fetched_final.type, "Global Technology")

        # Clean up
        OsintDataAccessLayer().delete_entity(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])

    def test_organization_crud_permission_denied(self):
        # Create an organization with a specific owner and roles
        org_data = OrganizationMainData(
            name="Protected Corp",
            type="Security",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_organization(org_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)

        # Test creating with insufficient permissions
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().create_organization(org_data, owner="non_admin_user", roles=[UserRole.USER])

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().get_organization(created.id, owner="another_user", roles=[UserRole.USER])

        # Test updating with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().update_organization(
                created.id, OrganizationMainData(type="Global Security"), owner="another_user", roles=[UserRole.USER]
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().delete_entity(created.id, owner="another_user", roles=[UserRole.ADMIN])

        # Clean up
        OsintDataAccessLayer().delete_entity(created.id, owner="owner_user", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
