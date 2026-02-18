import unittest

from omni_python_library import init_omni_library
from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.query_tools.entity_neighborhood import search_entity_neighborhood
from omni_python_library.dal.query_tools.event_search import search_events
from omni_python_library.models.osint import (
    EventMainData, LocationData, OrganizationMainData, PersonMainData, RelationMainData, SourceMainData, WebsiteMainData
)
from omni_python_library.utils import InternalError
from omni_python_library.utils.user import UserRole


class TestQueryTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_omni_library()

    def setUp(self):
        # Clear DB collections before each test
        for col_name in ArangoDBClient()._collections:
            ArangoDBClient()._collections[col_name].truncate()

    def test_search_events(self):
        # Create Events
        loc_us = LocationData(
            latitude=0.0,
            longitude=0.0,
            country_code="US",
            administrative_area="State",
            sub_administrative_area="County",
            locality="City",
            sub_locality="District",
            address="123 St",
            postal_code=12345,
        )
        loc_uk = LocationData(
            latitude=0.0,
            longitude=0.0,
            country_code="UK",
            administrative_area="County",
            sub_administrative_area="District",
            locality="London",
            sub_locality="Borough",
            address="10 Downing St",
            postal_code=54321,
        )

        e1_data = EventMainData(title="Event 1", description="First event", happened_at=1000, location=loc_us)
        e1 = OsintDataAccessLayer().create_event(e1_data, owner="test", roles=[UserRole.ADMIN])

        e2_data = EventMainData(title="Event 2", description="Second event", happened_at=2000, location=loc_us)
        e2 = OsintDataAccessLayer().create_event(e2_data, owner="test", roles=[UserRole.ADMIN])

        e3_data = EventMainData(
            title="Event 3", description="Third event (unrelated)", happened_at=3000, location=loc_uk
        )
        e3 = OsintDataAccessLayer().create_event(e3_data, owner="test", roles=[UserRole.ADMIN])

        e4_data = EventMainData(
            title="Event 4", description="Fourth event (other owner)", happened_at=4000, location=loc_us
        )
        e4 = OsintDataAccessLayer().create_event(e4_data, owner="other", roles=[UserRole.ADMIN])

        e5_data = EventMainData(
            title="Event 5", description="Fifth event (role access)", happened_at=5000, location=loc_us
        )
        e5 = OsintDataAccessLayer().create_event(e5_data, owner="other", roles=[UserRole.ADMIN])
        e5_doc = OsintDataAccessLayer().get_event(e5.id, owner="other", roles=[UserRole.ADMIN])
        e5_doc.read = [UserRole.ADMIN]
        OsintDataAccessLayer().update_event(id=e5.id, data=e5_doc, owner="other", roles=[UserRole.ADMIN])

        # Create Relation between E1 and E2
        rel_data = RelationMainData(name="link", from_id=e1.id, to_id=e2.id, label="related_to")
        OsintDataAccessLayer().create_relation(rel_data, owner="test", roles=[UserRole.ADMIN])

        # Search events (filter by country US to get E1 and E2)
        results = search_events(owner="test", roles=[UserRole.ADMIN], country_code="US")

        # Verify results
        event_ids = {r.id for r in results if r.id.startswith("event/")}
        relation_ids = {r.id for r in results if "event_link_event" in r.id}

        self.assertIn(e1.id, event_ids)
        self.assertIn(e2.id, event_ids)
        self.assertNotIn(e3.id, event_ids)
        self.assertNotIn(e4.id, event_ids)
        self.assertIn(e5.id, event_ids)

        # Check if relation is found
        self.assertTrue(len(relation_ids) > 0, "Should find relations between queried events")

        # Test date range filtering
        # Case 1: start and end
        results = search_events(owner="test", roles=[UserRole.ADMIN], country_code="US", date_range=(1500, 2500))
        event_ids = {r.id for r in results if r.id.startswith("event/")}
        self.assertEqual({e2.id}, event_ids)

        # Case 2: start only
        results = search_events(owner="test", roles=[UserRole.ADMIN], country_code="US", date_range=(1500, None))
        event_ids = {r.id for r in results if r.id.startswith("event/")}
        self.assertEqual({e2.id, e5.id}, event_ids)

        # Case 3: end only
        results = search_events(owner="test", roles=[UserRole.ADMIN], country_code="US", date_range=(None, 2500))
        event_ids = {r.id for r in results if r.id.startswith("event/")}
        self.assertEqual({e1.id, e2.id}, event_ids)

        # Case 4: no results
        results = search_events(owner="test", roles=[UserRole.ADMIN], country_code="US", date_range=(6000, 7000))
        event_ids = {r.id for r in results if r.id.startswith("event/")}
        self.assertEqual(set(), event_ids)

        # Case 5: all results in range
        results = search_events(owner="test", roles=[UserRole.ADMIN], country_code="US", date_range=(1000, 5000))
        event_ids = {r.id for r in results if r.id.startswith("event/")}
        self.assertEqual({e1.id, e2.id, e5.id}, event_ids)

    def test_search_entity_neighborhood(self):
        # Create Person
        p_data = PersonMainData(name="Alice", role="Analyst")
        p = OsintDataAccessLayer().create_person(p_data, owner="test", roles=[UserRole.ADMIN])

        p2_data = PersonMainData(name="Bob", role="Manager")
        p2 = OsintDataAccessLayer().create_person(p2_data, owner="other", roles=[UserRole.ADMIN])

        p3_data = PersonMainData(name="Charlie", role="Director")
        p3 = OsintDataAccessLayer().create_person(p3_data, owner="other", roles=[UserRole.ADMIN])
        p3_doc = OsintDataAccessLayer().get_person(p3.id, owner="other", roles=[UserRole.ADMIN])
        p3_doc.read = [UserRole.ADMIN]
        OsintDataAccessLayer().update_person(id=p3.id, data=p3_doc, owner="other", roles=[UserRole.ADMIN])

        # Create Event
        e_data = EventMainData(title="Incident A", happened_at=5000)
        e = OsintDataAccessLayer().create_event(e_data, owner="test", roles=[UserRole.ADMIN])

        # Create Organization
        org_data = OrganizationMainData(name="Evil Corp")
        org = OsintDataAccessLayer().create_organization(org_data, owner="test", roles=[UserRole.ADMIN])

        # Create Website
        web_data = WebsiteMainData(url="https://evil.com")
        web = OsintDataAccessLayer().create_website(web_data, owner="test", roles=[UserRole.ADMIN])

        # Create Source
        src_data = SourceMainData(url="https://news.com/article1")
        src = OsintDataAccessLayer().create_source(src_data, owner="test", roles=[UserRole.ADMIN])

        # Create another Event
        e2_data = EventMainData(title="Incident B", happened_at=6000)
        e2 = OsintDataAccessLayer().create_event(e2_data, owner="test", roles=[UserRole.ADMIN])

        # Create Relation Person -> Event
        rel_data = RelationMainData(name="participant", from_id=e.id, to_id=p.id, label="involved_in")
        OsintDataAccessLayer().create_relation(rel_data, owner="test", roles=[UserRole.ADMIN])

        rel2_data = RelationMainData(name="participant", from_id=e.id, to_id=p2.id, label="involved_in")
        OsintDataAccessLayer().create_relation(rel2_data, owner="test", roles=[UserRole.ADMIN])

        rel3_data = RelationMainData(name="participant", from_id=e.id, to_id=p3.id, label="involved_in")
        OsintDataAccessLayer().create_relation(rel3_data, owner="test", roles=[UserRole.ADMIN])

        # Create relations from the main event to other entities
        OsintDataAccessLayer().create_relation(
            RelationMainData(name="related", from_id=e.id, to_id=org.id, label="related_to"), owner="test", roles=[UserRole.ADMIN]
        )
        OsintDataAccessLayer().create_relation(
            RelationMainData(name="related", from_id=e.id, to_id=web.id, label="related_to"), owner="test", roles=[UserRole.ADMIN]
        )
        OsintDataAccessLayer().create_relation(
            RelationMainData(name="related", from_id=e.id, to_id=src.id, label="related_to"), owner="test", roles=[UserRole.ADMIN]
        )
        OsintDataAccessLayer().create_relation(
            RelationMainData(name="related", from_id=e.id, to_id=e2.id, label="related_to"), owner="test", roles=[UserRole.ADMIN]
        )

        # Search neighborhood of Event
        results = search_entity_neighborhood(e.id, owner="test", roles=[UserRole.ADMIN])

        ids = {r.id for r in results}
        self.assertIn(p.id, ids)
        self.assertNotIn(p2.id, ids)
        self.assertIn(p3.id, ids)
        self.assertIn(org.id, ids)
        self.assertIn(web.id, ids)
        self.assertIn(src.id, ids)
        self.assertNotIn(e2.id, ids)

    def test_search_entity_neighborhood_missing_bind_vars(self):
        with self.assertRaises(InternalError):
            OsintDataAccessLayer().query("FOR doc IN event RETURN doc", bind_vars={})

    def test_query_with_bad_query(self):
        with self.assertRaises(InternalError):
            OsintDataAccessLayer().query("FOR doc IN event RETUN doc", bind_vars={"owner": "test", "roles": [UserRole.ADMIN]})


if __name__ == "__main__":
    unittest.main()
