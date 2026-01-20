from typing import Any, Dict, List, Optional, Type, Union

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.osint_data_deleter import OsintDataDeleter
from omni_python_library.dal.osint_data_factory import OsintDataFactory
from omni_python_library.dal.osint_data_updater import OsintDataUpdater
from omni_python_library.models.osint import Event, Organization, Person, Relation, Source, Website


class OsintDataAccessLayer(OsintDataFactory, OsintDataUpdater, OsintDataDeleter):
    def init(self):
        super().init()

    def query(
        self, query_str: str, bind_vars: Optional[Dict[str, Any]] = None
    ) -> List[Union[Relation, Event, Source, Person, Organization, Website]]:
        """
        Executes an AQL query and returns a list of strongly-typed OSINT objects.

        :param query_str: The AQL query string. The query must return documents (dicts) compatible with the
                          OSINT models. Specifically:
                          - For Relations: The document must contain `_from` and `_to` fields.
                          - For Entities (Person, Organization, Website, Source, Event): The document must
                            contain an `_id` field in the format "collection_name/key", where "collection_name"
                            corresponds to one of the supported types (person, organization, website, source, event).

        Example:
            query_str = '''
                FOR doc IN person
                    FILTER doc.name == @name
                    RETURN doc
            '''
            results = dal.query(query_str, bind_vars={"name": "John Doe"})

        :param bind_vars: Optional dictionary of bind variables to substitute into the query string.
        :return: A list of mapped objects (Relation, Person, Organization, Website, Source, or Event).
                 Documents that do not match the expected schema or collection types are skipped.
        """
        if bind_vars is None:
            bind_vars = {}
        cursor = ArangoDBClient().db.aql.execute(query_str, bind_vars=bind_vars)
        results = []

        for doc in cursor:
            if not isinstance(doc, dict):
                continue

            if "_from" in doc and "_to" in doc:
                results.append(Relation(**doc))
                continue

            if "_id" in doc:
                col_name, _ = ArangoDBClient().parse_id(doc["_id"])
                if col_name == "person":
                    results.append(Person(**doc))
                elif col_name == "organization":
                    results.append(Organization(**doc))
                elif col_name == "website":
                    results.append(Website(**doc))
                elif col_name == "source":
                    results.append(Source(**doc))
                elif col_name == "event":
                    results.append(Event(**doc))

        return results

    def get_relation(self, id: str) -> Optional[Relation]:
        return self._get(Relation, id)

    def get_event(self, id: str) -> Optional[Event]:
        return self._get(Event, id)

    def get_source(self, id: str) -> Optional[Source]:
        return self._get(Source, id)

    def get_person(self, id: str) -> Optional[Person]:
        return self._get(Person, id)

    def get_organization(self, id: str) -> Optional[Organization]:
        return self._get(Organization, id)

    def get_website(self, id: str) -> Optional[Website]:
        return self._get(Website, id)

    def _get(
        self, model_cls: Type[Union[Relation, Event, Source, Person, Organization, Website]], id: str
    ) -> Optional[Any]:
        col_name, key = ArangoDBClient().parse_id(id)

        # Check cache
        cached_data = super().get(id)
        if cached_data:
            return model_cls(**cached_data)

        # Check DB
        collection = ArangoDBClient().get_collection(col_name)
        doc = collection.get({"_key": key})
        if doc:
            instance = model_cls(**doc)
            # Populate cache
            self.set(id, instance.model_dump(by_alias=True))
            return instance

        return None
