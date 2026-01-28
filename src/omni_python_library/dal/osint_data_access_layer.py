import logging
from typing import Any, Dict, List, Optional, Type, Union

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.osint_data_deleter import OsintDataDeleter
from omni_python_library.dal.osint_data_factory import OsintDataFactory
from omni_python_library.dal.osint_data_updater import OsintDataUpdater
from omni_python_library.models.osint import Event, Organization, Person, Relation, Source, Website
from omni_python_library.utils.config_registry import ArangoDBConstant, EntityNameConstant

logger = logging.getLogger(__name__)


class OsintDataAccessLayer(OsintDataFactory, OsintDataUpdater, OsintDataDeleter):
    def init(self):
        super().init()
        client = ArangoDBClient()
        client.init_collection(EntityNameConstant.PERSON, indices=[("inverted", "name")], vector_index=True)
        client.init_collection(EntityNameConstant.ORGANIZATION, indices=[("inverted", "name")], vector_index=True)
        client.init_collection(EntityNameConstant.WEBSITE, indices=[("persistent", "url")], vector_index=True)
        client.init_collection(EntityNameConstant.SOURCE, indices=[("persistent", "url")], vector_index=True)
        client.init_collection(
            EntityNameConstant.EVENT,
            indices=[
                ("inverted", "title"),
                ("inverted", "description"),
                ("persistent", "happened_at"),
                ("persistent", "location.country_code"),
            ],
            vector_index=True,
        )
        client.init_graph(
            ArangoDBConstant.EVENT_RELATED_GRAPH,
            lambda from_coll, to_coll: (
                ArangoDBConstant.EVENT_RELATED_GRAPH
                if from_coll == EntityNameConstant.EVENT and to_coll != EntityNameConstant.EVENT
                else None
            ),
        )
        client.init_graph(
            ArangoDBConstant.EVENT_GRAPH,
            lambda from_coll, to_coll: (
                ArangoDBConstant.EVENT_GRAPH
                if from_coll == EntityNameConstant.EVENT and to_coll == EntityNameConstant.EVENT
                else None
            ),
        )

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
        logger.debug(f"Executing query: {query_str} with vars: {bind_vars}")
        if bind_vars is None:
            bind_vars = {}
        try:
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

            logger.debug(f"Query returned {len(results)} results")
            return results
        except Exception:
            logger.exception("Error executing query")
            raise

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
        logger.debug(f"Getting {id}")
        doc = self._get_generic(id)
        if doc:
            return model_cls(**doc)
        return None

    def is_owner(self, data_id: str, user_id: str) -> bool:
        doc = self._get_generic(data_id)
        logger.debug(f"Checking ownership for {data_id}: user {user_id} == {doc.get('owner')}")
        return doc.get("owner") == user_id if doc else False

    def can_read(self, data_id: str, user_id: str, user_roles: List[str]) -> bool:
        doc = self._get_generic(data_id)
        logger.debug(
            f"Checking read permission for {data_id}: user {user_id}, roles {user_roles} in {doc.get('read', [])}"
        )
        if not doc:
            return False
        if doc.get("owner") == user_id:
            return True
        allowed = set(doc.get("read", []))
        return user_id in allowed or bool(allowed.intersection(user_roles))

    def can_write(self, data_id: str, user_id: str, user_roles: List[str]) -> bool:
        doc = self._get_generic(data_id)
        logger.debug(
            f"Checking write permission for {data_id}: user {user_id}, roles {user_roles} in {doc.get('write', [])}"
        )
        if not doc:
            return False
        if doc.get("owner") == user_id:
            return True
        allowed = set(doc.get("write", []))
        return user_id in allowed or bool(allowed.intersection(user_roles))

    def _get_generic(self, id: str) -> Optional[Dict[str, Any]]:
        cached_data = super().get(id)
        if cached_data:
            return cached_data

        try:
            col_name, key = ArangoDBClient().parse_id(id)
            collection = ArangoDBClient().get_collection(col_name)
            doc = collection.get({"_key": key})
            if doc:
                self.set(id, doc)
                return doc
        except Exception:
            logger.exception(f"Error fetching generic document {id}")
            pass
        return None
