import unittest

from omni_python_library.models.monitor import MonitoringSource, MonitoringSourceMainData
from omni_python_library.models.osint import (
    Event,
    EventMainData,
    Organization,
    OrganizationMainData,
    Person,
    PersonMainData,
    Relation,
    RelationMainData,
    Source,
    SourceMainData,
    Website,
    WebsiteMainData,
)
from omni_python_library.models.view import OsintView, OsintViewMainData


class TestModelDumpMain(unittest.TestCase):
    def test_relation_model_dump_main(self):
        relation = Relation(
            _id="relations/1",
            _key="1",
            _rev="rev",
            name="test",
            confidence=100,
            from_id="persons/1",
            to_id="organizations/1",
        )
        main_data = relation.model_dump_main()
        self.assertEqual(main_data["name"], "test")
        self.assertEqual(main_data["confidence"], 100)
        self.assertEqual(main_data["_from"], "persons/1")
        self.assertEqual(main_data["_to"], "organizations/1")
        self.assertNotIn("_id", main_data)
        self.assertNotIn("_key", main_data)
        self.assertNotIn("_rev", main_data)
        self.assertEqual(
            set(main_data.keys()), {field.alias or name for name, field in RelationMainData.model_fields.items()}
        )

    def test_event_model_dump_main(self):
        event = Event(
            _id="events/1",
            _key="1",
            _rev="rev",
            type="test_type",
            title="test_title",
        )
        main_data = event.model_dump_main()
        self.assertEqual(main_data["type"], "test_type")
        self.assertEqual(main_data["title"], "test_title")
        self.assertNotIn("_id", main_data)
        self.assertNotIn("_key", main_data)
        self.assertNotIn("_rev", main_data)
        self.assertEqual(set(main_data.keys()), set(EventMainData.model_fields.keys()))

    def test_source_model_dump_main(self):
        source = Source(
            _id="sources/1",
            _key="1",
            _rev="rev",
            type="test_type",
            name="test_name",
        )
        main_data = source.model_dump_main()
        self.assertEqual(main_data["type"], "test_type")
        self.assertEqual(main_data["name"], "test_name")
        self.assertNotIn("_id", main_data)
        self.assertNotIn("_key", main_data)
        self.assertNotIn("_rev", main_data)
        self.assertEqual(set(main_data.keys()), set(SourceMainData.model_fields.keys()))

    def test_person_model_dump_main(self):
        person = Person(
            _id="persons/1",
            _key="1",
            _rev="rev",
            name="test_name",
            role="test_role",
        )
        main_data = person.model_dump_main()
        self.assertEqual(main_data["name"], "test_name")
        self.assertEqual(main_data["role"], "test_role")
        self.assertNotIn("_id", main_data)
        self.assertNotIn("_key", main_data)
        self.assertNotIn("_rev", main_data)
        self.assertEqual(set(main_data.keys()), set(PersonMainData.model_fields.keys()))

    def test_organization_model_dump_main(self):
        organization = Organization(
            _id="organizations/1",
            _key="1",
            _rev="rev",
            name="test_name",
            type="test_type",
        )
        main_data = organization.model_dump_main()
        self.assertEqual(main_data["name"], "test_name")
        self.assertEqual(main_data["type"], "test_type")
        self.assertNotIn("_id", main_data)
        self.assertNotIn("_key", main_data)
        self.assertNotIn("_rev", main_data)
        self.assertEqual(set(main_data.keys()), set(OrganizationMainData.model_fields.keys()))

    def test_website_model_dump_main(self):
        website = Website(
            _id="websites/1",
            _key="1",
            _rev="rev",
            url="http://test.com",
            title="test_title",
        )
        main_data = website.model_dump_main()
        self.assertEqual(main_data["url"], "http://test.com")
        self.assertEqual(main_data["title"], "test_title")
        self.assertNotIn("_id", main_data)
        self.assertNotIn("_key", main_data)
        self.assertNotIn("_rev", main_data)
        self.assertEqual(set(main_data.keys()), set(WebsiteMainData.model_fields.keys()))

    def test_osint_view_model_dump_main(self):
        osint_view = OsintView(
            _id="osint_views/1",
            _key="1",
            _rev="rev",
            name="test_name",
            description="test_description",
        )
        main_data = osint_view.model_dump_main()
        self.assertEqual(main_data["name"], "test_name")
        self.assertEqual(main_data["description"], "test_description")
        self.assertNotIn("_id", main_data)
        self.assertNotIn("_key", main_data)
        self.assertNotIn("_rev", main_data)
        self.assertEqual(set(main_data.keys()), set(OsintViewMainData.model_fields.keys()))

    def test_monitoring_source_model_dump_main(self):
        monitoring_source = MonitoringSource(
            _id="monitoring_sources/1",
            _key="1",
            _rev="rev",
            name="test_name",
            url="http://test.com",
            owner="test_owner",
        )
        main_data = monitoring_source.model_dump_main()
        self.assertEqual(main_data["name"], "test_name")
        self.assertEqual(main_data["url"], "http://test.com")
        self.assertNotIn("_id", main_data)
        self.assertNotIn("_key", main_data)
        self.assertNotIn("_rev", main_data)
        self.assertEqual(set(main_data.keys()), set(MonitoringSourceMainData.model_fields.keys()))
