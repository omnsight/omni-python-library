import logging
from typing import Any, Dict, List, Optional, Union

from omni_python_library.clients import PENDING_UPDATES, ArangoDBClient
from omni_python_library.dal.osint import OsintDataDestroyer, OsintDataFactory, OsintDataMutator
from omni_python_library.models import Event, Organization, Person, Relation, Source, Website
from omni_python_library.utils import ArangoDBConstant, EntityNameConstant, InternalError

logger = logging.getLogger(__name__)


class OsintDataAccessLayer(OsintDataFactory, OsintDataMutator, OsintDataDestroyer):
    def init(self):
        super().init()
        ArangoDBClient().init_collection(EntityNameConstant.PERSON, indices=[("inverted", "name")], vector_index=True)
        ArangoDBClient().init_collection(
            EntityNameConstant.ORGANIZATION, indices=[("inverted", "name")], vector_index=True
        )
        ArangoDBClient().init_collection(EntityNameConstant.WEBSITE, indices=[("persistent", "url")], vector_index=True)
        ArangoDBClient().init_collection(EntityNameConstant.SOURCE, indices=[("persistent", "url")], vector_index=True)
        ArangoDBClient().init_collection(
            EntityNameConstant.EVENT,
            indices=[
                ("inverted", "title"),
                ("inverted", "description"),
                ("persistent", "happened_at"),
                ("persistent", "location.country_code"),
            ],
            vector_index=True,
        )
        ArangoDBClient().init_graph(
            ArangoDBConstant.EVENT_RELATED_GRAPH,
            lambda from_coll, to_coll: (
                ArangoDBConstant.EVENT_RELATED_GRAPH
                if from_coll == EntityNameConstant.EVENT and to_coll != EntityNameConstant.EVENT
                else None
            ),
        )
        ArangoDBClient().init_graph(
            ArangoDBConstant.EVENT_GRAPH,
            lambda from_coll, to_coll: (
                ArangoDBConstant.EVENT_GRAPH
                if from_coll == EntityNameConstant.EVENT and to_coll == EntityNameConstant.EVENT
                else None
            ),
        )

    def query(
        self,
        query_str: str,
        bind_vars: Dict[str, Any],
        in_pending: bool = False,
    ) -> List[Union[Relation, Event, Source, Person, Organization, Website]]:
        """
        Executes an AQL query and returns a list of strongly-typed OSINT objects.

        :param query_str: The AQL query string.
        :param bind_vars: Optional dictionary of bind variables.
        :return: A list of mapped objects.
        """
        logger.debug(f"Executing query: {query_str} with vars: {bind_vars}")

        if "owner" not in bind_vars or "roles" not in bind_vars:
            raise InternalError("bind_vars must contain owner and roles")

        try:
            cursor = ArangoDBClient().db.aql.execute(query_str, bind_vars=bind_vars)
            results = []

            for doc in cursor:
                if not isinstance(doc, dict) or not doc.get("_id"):
                    continue

                pending = self.get(doc["_id"], db=PENDING_UPDATES) or {} if in_pending else {}

                if "_from" in doc and "_to" in doc:
                    results.append(Relation(**{**doc, **pending}))
                else:
                    col_name, _ = ArangoDBClient().parse_id(doc["_id"])
                    if col_name == EntityNameConstant.PERSON:
                        results.append(Person(**{**doc, **pending}))
                    elif col_name == EntityNameConstant.ORGANIZATION:
                        results.append(Organization(**{**doc, **pending}))
                    elif col_name == EntityNameConstant.WEBSITE:
                        results.append(Website(**{**doc, **pending}))
                    elif col_name == EntityNameConstant.SOURCE:
                        results.append(Source(**{**doc, **pending}))
                    elif col_name == EntityNameConstant.EVENT:
                        results.append(Event(**{**doc, **pending}))

            logger.debug(f"Query returned {len(results)} results")
            return results
        except Exception as e:
            raise InternalError("Error executing query") from e
