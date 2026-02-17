import unittest

from omni_python_library import init_omni_library
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import PersonMainData
from omni_python_library.utils import PermissionDeniedError
from omni_python_library.utils.user import UserRole


class TestPersonCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def test_person_crud(self):
        # Create
        person_data = PersonMainData(
            name="John Doe",
            role="Engineer",
            nationality="US",
            birth_date=100000,
            updated_at=200000,
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )

        created = OsintDataAccessLayer().create_person(person_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.name, "John Doe")

        # Read
        fetched = OsintDataAccessLayer().get_person(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "John Doe")
        self.assertEqual(fetched.role, "Engineer")

        # Update
        updated = OsintDataAccessLayer().update_person(
            created.id, PersonMainData(role="Senior Engineer"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated.role, "Senior Engineer")

        # Read again (should hit cache or DB)
        fetched_updated = OsintDataAccessLayer().get_person(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_updated.role, "Senior Engineer")

        # Delete
        deleted = OsintDataAccessLayer().delete_entity(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertTrue(deleted)

        # Verify Delete
        fetched_deleted = OsintDataAccessLayer().get_person(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(fetched_deleted)

    def test_person_crud_with_pending(self):
        # Create
        person_data = PersonMainData(
            name="Jane Doe",
            role="Analyst",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_person(person_data, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.name, "Jane Doe")

        # Update with in_pending=True
        OsintDataAccessLayer().update_person(
            created.id,
            PersonMainData(role="Senior Analyst"),
            owner="test_user_pending",
            roles=[UserRole.ADMIN],
            in_pending=True,
        )

        # Read with in_pending=False (default) - should get original data
        fetched_not_pending = OsintDataAccessLayer().get_person(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(fetched_not_pending.role, "Analyst")

        # Read with in_pending=True - should get merged data
        fetched_pending = OsintDataAccessLayer().get_person(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertEqual(fetched_pending.role, "Senior Analyst")
        self.assertEqual(fetched_pending.name, "Jane Doe")  # Ensure other fields are intact

        # Perform a final update (in_pending=False)
        final_update = OsintDataAccessLayer().update_person(
            created.id, PersonMainData(nationality="CA"), owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(final_update.nationality, "CA")
        self.assertEqual(final_update.role, "Senior Analyst")  # Check that pending change was applied

        # Read again, should be permanently updated
        fetched_final = OsintDataAccessLayer().get_person(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_final.nationality, "CA")
        self.assertEqual(fetched_final.role, "Senior Analyst")

        # Clean up
        OsintDataAccessLayer().delete_entity(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])

    def test_person_crud_permission_denied(self):
        # Create a person with a specific owner and roles
        person_data = PersonMainData(
            name="Protected Person",
            role="VIP",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_person(person_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)

        # Test creating with insufficient permissions
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().create_person(person_data, owner="non_admin_user", roles=[UserRole.USER])

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().get_person(created.id, owner="another_user", roles=[UserRole.USER])

        # Test updating with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().update_person(
                created.id, PersonMainData(role="Super VIP"), owner="another_user", roles=[UserRole.USER]
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().delete_entity(created.id, owner="another_user", roles=[UserRole.ADMIN])

        # Clean up
        OsintDataAccessLayer().delete_entity(created.id, owner="owner_user", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
