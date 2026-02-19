import unittest

from omni_python_library import init_omni_library
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.osint import PersonMainData, RelationMainData
from omni_python_library.utils import PermissionDeniedError
from omni_python_library.utils.user import UserRole


class TestRelationCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def setUp(self):
        # Create entities to be related
        person1_data = PersonMainData(name="Person 1", read=[UserRole.ADMIN], write=[UserRole.ADMIN])
        person2_data = PersonMainData(name="Person 2", read=[UserRole.ADMIN], write=[UserRole.ADMIN])
        self.person1 = OsintDataAccessLayer().create_person(person1_data, owner="test_user", roles=[UserRole.ADMIN])
        self.person2 = OsintDataAccessLayer().create_person(person2_data, owner="test_user", roles=[UserRole.ADMIN])

    def test_relation_crud(self):
        # Create
        relation_data = RelationMainData(
            from_id=self.person1.id,
            to_id=self.person2.id,
            name="knows",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )

        created = OsintDataAccessLayer().create_relation(relation_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)
        self.assertEqual(created.name, "knows")

        # Read
        fetched = OsintDataAccessLayer().get_relation(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "knows")

        # Update
        updated = OsintDataAccessLayer().update_relation(
            created.id, RelationMainData(name="friends_with"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated.name, "friends_with")

        # Read again
        fetched_updated = OsintDataAccessLayer().get_relation(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched_updated.name, "friends_with")

        # Delete
        OsintDataAccessLayer().delete_relation(created.id, owner="test_user", roles=[UserRole.ADMIN])

        # Verify Delete
        fetched_deleted = OsintDataAccessLayer().get_relation(created.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(fetched_deleted)

    def test_relation_crud_with_pending(self):
        # Create
        relation_data = RelationMainData(
            from_id=self.person1.id,
            to_id=self.person2.id,
            name="colleagues",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_relation(
            relation_data, owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertIsNotNone(created)
        self.assertEqual(created.name, "colleagues")

        # Update with in_pending=True
        OsintDataAccessLayer().update_relation(
            created.id,
            RelationMainData(name="reports_to"),
            owner="test_user_pending",
            roles=[UserRole.ADMIN],
            in_pending=True,
        )

        # Read with in_pending=False (default) - should get original data
        fetched_not_pending = OsintDataAccessLayer().get_relation(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(fetched_not_pending.name, "colleagues")

        # Read with in_pending=True - should get merged data
        fetched_pending = OsintDataAccessLayer().get_relation(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN], in_pending=True
        )
        self.assertEqual(fetched_pending.name, "reports_to")

        # Perform a final update (in_pending=False)
        final_update = OsintDataAccessLayer().update_relation(
            created.id, RelationMainData(name="manager_of"), owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(final_update.name, "manager_of")

        # Read again, should be permanently updated
        fetched_final = OsintDataAccessLayer().get_relation(
            created.id, owner="test_user_pending", roles=[UserRole.ADMIN]
        )
        self.assertEqual(fetched_final.name, "manager_of")

        # Clean up
        OsintDataAccessLayer().delete_relation(created.id, owner="test_user_pending", roles=[UserRole.ADMIN])

    def test_relation_crud_permission_denied(self):
        # Create a relation with a specific owner and roles
        relation_data = RelationMainData(
            from_id=self.person1.id,
            to_id=self.person2.id,
            name="secure_knows",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = OsintDataAccessLayer().create_relation(relation_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)

        # Test creating with insufficient permissions
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().create_relation(relation_data, owner="non_admin_user", roles=[UserRole.USER])

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().get_relation(created.id, owner="another_user", roles=[UserRole.USER])

        # Test updating with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().update_relation(
                created.id, RelationMainData(name="secure_friends_with"), owner="another_user", roles=[UserRole.USER]
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            OsintDataAccessLayer().delete_relation(created.id, owner="another_user", roles=[UserRole.ADMIN])

        # Clean up
        OsintDataAccessLayer().delete_relation(created.id, owner="owner_user", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
