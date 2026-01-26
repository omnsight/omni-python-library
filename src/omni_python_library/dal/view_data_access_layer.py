import logging
from typing import Dict, List, Optional, Any

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view_data_deleter import ViewDataDeleter
from omni_python_library.dal.view_data_factory import ViewDataFactory
from omni_python_library.dal.view_data_updater import ViewDataUpdater
from omni_python_library.models.view import OsintView
from omni_python_library.models.osint import Event, Organization, Person, Relation, Source, Website

logger = logging.getLogger(__name__)

COLLECTION_NAME = "osintview"
VIEW_GRAPH_NAME = "osint_graph"


class ViewDataAccessLayer(ViewDataFactory, ViewDataUpdater, ViewDataDeleter):
    def __init__(self):
        super().__init__()
        client = ArangoDBClient()
        client.init_collection(
            COLLECTION_NAME,
            indices=[("inverted", "name"), ("inverted", "description")],
            vector_index=False,
        )
        client.init_graph(
            VIEW_GRAPH_NAME, lambda from_coll, to_coll: VIEW_GRAPH_NAME if from_coll == COLLECTION_NAME else None
        )

    def get_view(self, id: str) -> Optional[OsintView]:
        logger.debug(f"Getting view {id}")
        doc = self._get_generic(id)
        if doc:
            return OsintView(**doc)
        return None

    def query_views(self, text: str, owner: str, lang: str = "en", limit: int = 100) -> List[OsintView]:
        logger.debug(f"Querying views by text: {text} and owner: {owner}")

        query = f"""
            LET terms = TOKENS(@text, "text_{lang}")
            FOR doc IN osintview
                SEARCH ANALYZER(
                    MIN_MATCH(
                        doc.name IN terms,
                        doc.description IN terms,
                        LENGTH(terms)
                    ),
                    f"text_{lang}"
                )
                FILTER doc.owner == @owner
                LIMIT @limit
                RETURN doc
        """

        bind_vars = {"text": text, "owner": owner, "limit": limit}
        try:
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
            results = []
            for doc in cursor:
                if isinstance(doc, dict):
                    results.append(OsintView(**doc))
            return results
        except Exception:
            logger.exception("Error querying views by text")
            raise

    def get_entities(self, view_id: str) -> List[Relation | Event | Source | Person | Organization | Website]:
        logger.debug(f"Querying entities connected to view: {view_id}")

        query = f"""
            FOR v, e IN 1..1 OUTBOUND @view_id
                GRAPH '{VIEW_GRAPH_NAME}'
                RETURN v
        """
        bind_vars = {"view_id": view_id}
        return OsintDataAccessLayer().query(query, bind_vars=bind_vars)

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
