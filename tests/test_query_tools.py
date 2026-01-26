import unittest
import time
from arango import ArangoClient as PyArangoClient
from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.clients.redis import RedisClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.query_tools.event_search import search_events
from omni_python_library.dal.query_tools.entity_neighborhood import search_entity_neighborhood
from omni_python_library.models.osint import EventMainData, RelationMainData, PersonMainData, LocationData
from omni_python_library.utils.singleton import Singleton

from omni_python_library.clients.openai import OpenAIClient


class TestQueryTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Singleton._instances = {}

        # Initialize OpenAIClient to avoid attribute errors
        OpenAIClient().init()

        # Initialize Redis
        try:
            RedisClient().init(host="localhost", port=6379, db=0)
            RedisClient().client.flushdb()
        except Exception as e:
            print(f"Redis not available: {e}")
            raise unittest.SkipTest("Redis service not available")

        # Initialize ArangoDB
        try:
            sys_client = PyArangoClient(hosts="http://localhost:8529")
            sys_db = sys_client.db("_system", username="root", password="")

            if sys_db.has_database("test_osint_db_query"):
                sys_db.delete_database("test_osint_db_query")

            sys_db.create_database("test_osint_db_query")

            ArangoDBClient().init(
                host="http://localhost:8529", username="root", password="", db_name="test_osint_db_query"
            )
        except Exception as e:
            print(f"ArangoDB not available: {e}")
            raise unittest.SkipTest("ArangoDB service not available")

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
        e1 = self.dal.create_event(e1_data, owner="test")

        e2_data = EventMainData(title="Event 2", description="Second event", happened_at=2000, location=loc_us)
        e2 = self.dal.create_event(e2_data, owner="test")

        e3_data = EventMainData(
            title="Event 3", description="Third event (unrelated)", happened_at=3000, location=loc_uk
        )
        e3 = self.dal.create_event(e3_data, owner="test")

        # Create Relation between E1 and E2
        # Note: We need to use a name that will be picked up by the graph logic.
        # Based on OsintDataAccessLayer.init, EVENT_GRAPH_NAME logic seems tricky.
        # But let's try with "link" and see if it works, or if we need to fix the DAL.
        rel_data = RelationMainData(name="link", from_id=e1.id, to_id=e2.id, label="related_to")
        self.dal.create_relation(rel_data, owner="test")

        # Search events (filter by country US to get E1 and E2)
        results = search_events(country_code="US")

        # Verify results
        # We expect E1, E2 and the relation between them.
        event_ids = [r.id for r in results if r.id.startswith("event/")]
        relation_ids = [r.id for r in results if "event_link_event" in r.id]

        self.assertIn(e1.id, event_ids)
        self.assertIn(e2.id, event_ids)
        self.assertNotIn(e3.id, event_ids)

        # Check if relation is found
        # If the graph configuration is buggy, this might fail (relation_ids might be empty)
        self.assertTrue(len(relation_ids) > 0, "Should find relations between queried events")

    def test_search_entity_neighborhood(self):
        # Create Person
        p_data = PersonMainData(name="Alice", role="Analyst")
        p = self.dal.create_person(p_data, owner="test")

        # Create Event
        e_data = EventMainData(title="Incident A", happened_at=5000)
        e = self.dal.create_event(e_data, owner="test")

        # Create Relation Person -> Event
        # This should be in EVENT_RELATED_GRAPH_NAME
        rel_data = RelationMainData(
            name="participant", from_id=e.id, to_id=p.id, label="involved_in"  # Event -> Person? Or Person -> Event?
        )
        # Note: EVENT_RELATED_GRAPH_NAME logic in DAL: from_coll == EVENT_COLLECTION_NAME and to_coll != EVENT_COLLECTION_NAME
        # So we must go FROM Event TO Person for it to be added to the graph automatically.

        self.dal.create_relation(rel_data, owner="test")

        # Search neighborhood of Event
        results = search_entity_neighborhood(e.id)

        ids = [r.id for r in results]
        self.assertIn(p.id, ids)


if __name__ == "__main__":
    unittest.main()
