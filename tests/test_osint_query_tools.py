import time
import unittest

from arango import ArangoClient as PyArangoClient

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.openai import OpenAIClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.query_tools.entity_neighborhood import search_entity_neighborhood
from omni_python_library.dal.query_tools.event_search import search_events
from omni_python_library.models.osint import EventMainData, LocationData, PersonMainData, RelationMainData
from omni_python_library.utils import InternalError
from omni_python_library.utils.singleton import Singleton
from omni_python_library.utils.user import UserRole


class TestQueryTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Singleton._instances = {}

        # Initialize OpenAIClient to avoid attribute errors
        OpenAIClient().init()

        RedisClient().init(host="localhost", port=6379)
        # Clear Redis
        RedisClient().client.flushdb()

        # Create DB if not exists using direct client to avoid initializing collections in _system
        sys_client = PyArangoClient(hosts="http://localhost:8529")
        sys_db = sys_client.db("_system", username="root", password="password")

        # Drop existing DB to ensure clean state
        if sys_db.has_database("test_osint_db"):
            sys_db.delete_database("test_osint_db")

        sys_db.create_database("test_osint_db")

        # Now initialize the application client
        ArangoDBClient().init(
            host="http://localhost:8529", username="root", password="password", db_name="test_osint_db"
        )

    def setUp(self):
        self.dal = OsintDataAccessLayer()
        # Initialize DAL (creates collections and graphs)
        self.dal.init()

        # Clear collections (if needed, or relying on unique DB per run)
        # Since we use a fresh DB in setUpClass, we might just need to ensure cleanliness if we reuse it.
        # But for now, let's assume it's clean enough or we clean up after.
        # Actually, let's just truncate collections to be safe between tests.
        client = ArangoDBClient()
        for col_name in client._collections:
            client._collections[col_name].truncate()

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
        e1 = self.dal.create_event(e1_data, owner="test", roles=[UserRole.ADMIN])

        e2_data = EventMainData(title="Event 2", description="Second event", happened_at=2000, location=loc_us)
        e2 = self.dal.create_event(e2_data, owner="test", roles=[UserRole.ADMIN])

        e3_data = EventMainData(
            title="Event 3", description="Third event (unrelated)", happened_at=3000, location=loc_uk
        )
        e3 = self.dal.create_event(e3_data, owner="test", roles=[UserRole.ADMIN])

        e4_data = EventMainData(
            title="Event 4", description="Fourth event (other owner)", happened_at=4000, location=loc_us
        )
        e4 = self.dal.create_event(e4_data, owner="other", roles=[UserRole.ADMIN])

        e5_data = EventMainData(
            title="Event 5", description="Fifth event (role access)", happened_at=5000, location=loc_us
        )
        e5 = self.dal.create_event(e5_data, owner="other", roles=[UserRole.ADMIN])
        e5_doc = self.dal.get_event(e5.id, owner="other", roles=[UserRole.ADMIN])
        e5_doc.read = [UserRole.ADMIN]
        self.dal.update_event(id=e5.id, data=e5_doc, owner="other", roles=[UserRole.ADMIN])

        # Create Relation between E1 and E2
        rel_data = RelationMainData(name="link", from_id=e1.id, to_id=e2.id, label="related_to")
        self.dal.create_relation(rel_data, owner="test", roles=[UserRole.ADMIN])

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

    def test_search_entity_neighborhood(self):
        # Create Person
        p_data = PersonMainData(name="Alice", role="Analyst")
        p = self.dal.create_person(p_data, owner="test", roles=[UserRole.ADMIN])

        p2_data = PersonMainData(name="Bob", role="Manager")
        p2 = self.dal.create_person(p2_data, owner="other", roles=[UserRole.ADMIN])

        p3_data = PersonMainData(name="Charlie", role="Director")
        p3 = self.dal.create_person(p3_data, owner="other", roles=[UserRole.ADMIN])
        p3_doc = self.dal.get_person(p3.id, owner="other", roles=[UserRole.ADMIN])
        p3_doc.read = [UserRole.ADMIN]
        self.dal.update_person(id=p3.id, data=p3_doc, owner="other", roles=[UserRole.ADMIN])

        # Create Event
        e_data = EventMainData(title="Incident A", happened_at=5000)
        e = self.dal.create_event(e_data, owner="test", roles=[UserRole.ADMIN])

        # Create Relation Person -> Event
        rel_data = RelationMainData(name="participant", from_id=e.id, to_id=p.id, label="involved_in")
        self.dal.create_relation(rel_data, owner="test", roles=[UserRole.ADMIN])

        rel2_data = RelationMainData(name="participant", from_id=e.id, to_id=p2.id, label="involved_in")
        self.dal.create_relation(rel2_data, owner="test", roles=[UserRole.ADMIN])

        rel3_data = RelationMainData(name="participant", from_id=e.id, to_id=p3.id, label="involved_in")
        self.dal.create_relation(rel3_data, owner="test", roles=[UserRole.ADMIN])

        # Search neighborhood of Event
        results = search_entity_neighborhood(e.id, owner="test", roles=[UserRole.ADMIN])

        ids = {r.id for r in results}
        self.assertIn(p.id, ids)
        self.assertNotIn(p2.id, ids)
        self.assertIn(p3.id, ids)

    def test_search_entity_neighborhood_missing_bind_vars(self):
        with self.assertRaises(InternalError):
            self.dal.query("FOR doc IN event RETURN doc", bind_vars={})


if __name__ == "__main__":
    unittest.main()
