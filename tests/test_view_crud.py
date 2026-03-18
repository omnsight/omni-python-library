import logging
import unittest

from omni_python_library import init_omni_library
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view_data_access_layer import ViewDataAccessLayer
from omni_python_library.models.osint import PersonMainData
from omni_python_library.models.view import OsintViewMainData
from omni_python_library.utils.config import UserRole
from omni_python_library.utils.errors import InternalError, NotFoundError, PermissionDeniedError

# Configure logging
logging.basicConfig(level=logging.DEBUG)


class TestViewCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def test_view_lifecycle(self):
        # Create a person to be used in view
        person_data = PersonMainData(name="Test Person", role="Tester", nationality="US")
        person = OsintDataAccessLayer().create_person(person_data, owner="test_user", roles=[UserRole.ADMIN])

        # Create View
        analysis = [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello world!",
                    }
                ],
            }
        ]
        view_data = OsintViewMainData(name="Test View", description="Description", analysis=analysis)
        view = ViewDataAccessLayer().create_view(view_data, owner="test_user", roles=[UserRole.ADMIN])

        self.assertIsNotNone(view.id)
        self.assertEqual(view.name, "Test View")
        self.assertEqual(len(view.analysis), len(analysis))

        # Get View
        fetched = ViewDataAccessLayer().get_view(view.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(fetched.name, "Test View")
        self.assertEqual(len(fetched.analysis), len(analysis))

        # Update View (top level)
        updated_view = ViewDataAccessLayer().update_view(
            view.id, OsintViewMainData(description="Updated Description"), owner="test_user", roles=[UserRole.ADMIN]
        )
        self.assertEqual(updated_view.description, "Updated Description")

        # Connect Entity to View (to the second config, index 1)
        ViewDataAccessLayer().connect_entity_to_view(view.id, person.id, owner="test_user", roles=[UserRole.ADMIN])
        entities = ViewDataAccessLayer().get_entities(view.id, owner="test_user", roles=[UserRole.ADMIN])
        assert any(entity.id == person.id for entity in entities)

        # Remove Entity from View
        ViewDataAccessLayer().remove_entity_from_view(view.id, person.id, owner="test_user", roles=[UserRole.ADMIN])
        entities = ViewDataAccessLayer().get_entities(view.id, owner="test_user", roles=[UserRole.ADMIN])
        assert all(entity.id != person.id for entity in entities)
        assert len(entities) == 0

        # Query by Text
        views = ViewDataAccessLayer().query_views("Test View", "test_user")
        self.assertTrue(any(v.id == view.id for v in views))

        # Query by Description
        views = ViewDataAccessLayer().query_views("Updated Description", "test_user")
        self.assertTrue(any(v.id == view.id for v in views))

        # Query without text
        views = ViewDataAccessLayer().query_views(None, "test_user")
        self.assertTrue(any(v.id == view.id for v in views))

        # Delete View
        ViewDataAccessLayer().delete_view(view.id, owner="test_user", roles=[UserRole.ADMIN])
        self.assertIsNone(ViewDataAccessLayer().get_view(view.id, owner="test_user", roles=[UserRole.ADMIN]))

    def test_add_analysis_to_view(self):
        person_data = PersonMainData(name="Test Person", role="Tester", nationality="US")
        person = OsintDataAccessLayer().create_person(person_data, owner="test_user", roles=[UserRole.ADMIN])

        view_data = OsintViewMainData(name="Test View", description="Description", analysis=[])
        view = ViewDataAccessLayer().create_view(view_data, owner="test_user", roles=[UserRole.ADMIN])

        view_data = OsintViewMainData(description="Description Updated")
        updated_view = ViewDataAccessLayer().update_view(view.id, view_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(updated_view.description, "Description Updated")
        self.assertEqual(len(updated_view.analysis), 0)

        analysis = [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello world!",
                    }
                ],
            }
        ]
        view_data = OsintViewMainData(analysis=analysis)
        updated_view2 = ViewDataAccessLayer().update_view(view.id, view_data, owner="test_user", roles=[UserRole.ADMIN])
        self.assertEqual(len(updated_view2.analysis), 1)

    def test_update_view_with_invalid_entity(self):
        # Create view first
        view_data = OsintViewMainData(name="Test View 2", description="Description", analysis=[])
        view = ViewDataAccessLayer().create_view(view_data, owner="test_user", roles=[UserRole.ADMIN])

        with self.assertRaises(NotFoundError):
            ViewDataAccessLayer().connect_entity_to_view(
                view.id, "person/non_existent_123", owner="test_user", roles=[UserRole.ADMIN]
            )

    def test_view_crud_permission_denied(self):
        # Create a view with a specific owner and roles
        view_data = OsintViewMainData(
            name="Protected View",
            description="A view with restricted access",
            read=[UserRole.ADMIN],
            write=[UserRole.ADMIN],
        )
        created = ViewDataAccessLayer().create_view(view_data, owner="owner_user", roles=[UserRole.ADMIN])
        self.assertIsNotNone(created)

        # Test creating with insufficient permissions
        with self.assertRaises(PermissionDeniedError):
            ViewDataAccessLayer().create_view(view_data, owner="non_admin_user", roles=[UserRole.USER])

        # Test reading with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            ViewDataAccessLayer().get_view(created.id, owner="another_user", roles=[UserRole.USER])

        # Test updating with wrong owner and no matching roles
        with self.assertRaises(PermissionDeniedError):
            ViewDataAccessLayer().update_view(
                created.id,
                OsintViewMainData(description="Updated by wrong user"),
                owner="another_user",
                roles=[UserRole.USER],
            )

        # Test deleting with wrong owner
        with self.assertRaises(PermissionDeniedError):
            ViewDataAccessLayer().delete_view(created.id, owner="another_user", roles=[UserRole.ADMIN])

        # Clean up
        ViewDataAccessLayer().delete_view(created.id, owner="owner_user", roles=[UserRole.ADMIN])

    def test_query_views_with_invalid_limit(self):
        with self.assertRaises(InternalError):
            ViewDataAccessLayer().query_views("any", owner="test_user", limit=-1)

    def test_view_get_entities_permission_denied(self):
        with self.assertRaises(NotFoundError):
            ViewDataAccessLayer().get_entities("bad_id", owner="test_user", roles=[UserRole.ADMIN])


if __name__ == "__main__":
    unittest.main()
