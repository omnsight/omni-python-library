import logging
from typing import List

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.view import ViewDataDestroyer, ViewDataFactory, ViewDataMutator
from omni_python_library.models import OsintView
from omni_python_library.utils.config import ArangoDBConstant, EntityNameConstant
from omni_python_library.utils.errors import InternalError

logger = logging.getLogger(__name__)


class ViewDataAccessLayer(ViewDataFactory, ViewDataMutator, ViewDataDestroyer):
    def init(self):
        super().init()
        ArangoDBClient().init_collection(
            EntityNameConstant.VIEW,
            indices=[],
            vector_index=False,
        )
        # Create inverted index with text_en analyzer for search
        try:
            col = ArangoDBClient().get_collection(EntityNameConstant.VIEW)
            col.add_index(
                {
                    "type": "inverted",
                    "fields": ["name", "description"],
                    "analyzer": "text_en",
                }
            )
        except Exception as e:
            logger.warning(f"Failed to create inverted index on {EntityNameConstant.VIEW}: {e}")

        ArangoDBClient().init_graph(
            ArangoDBConstant.VIEW_GRAPH,
            [
                EntityNameConstant.VIEW,
                EntityNameConstant.MONITORING_SOURCE,
                EntityNameConstant.PERSON,
                EntityNameConstant.ORGANIZATION,
                EntityNameConstant.WEBSITE,
                EntityNameConstant.SOURCE,
                EntityNameConstant.EVENT,
            ],
            lambda from_coll, to_coll: (
                ArangoDBConstant.VIEW_GRAPH
                if from_coll in [EntityNameConstant.VIEW, EntityNameConstant.MONITORING_SOURCE]
                else None
            ),
        )

    def query_views(self, text: str | None, owner: str, limit: int = 100, offset: int = 0) -> List[OsintView]:
        logger.debug(f"Querying views by text: {text}, owner: {owner}, limit: {limit}, offset: {offset}")

        # Use FILTER instead of SEARCH to avoid "collection or view not found" error with inverted index
        text_filter = ""
        if text:
            text_filter = (
                "FILTER (CONTAINS(LOWER(doc.name), LOWER(@text)) OR CONTAINS(LOWER(doc.description), LOWER(@text)))"
            )

        query = f"""
            FOR doc IN {EntityNameConstant.VIEW}
                {text_filter}
                FILTER doc.owner == @owner
                LIMIT @offset, @limit
                RETURN doc
        """

        bind_vars = {"owner": owner, "limit": limit, "offset": offset}
        if text:
            bind_vars["text"] = text

        try:
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
            results = []
            for doc in cursor:
                results.append(OsintView(**doc))
            return results
        except Exception as e:
            logger.error(f"Error executing AQL: {e}")
            raise InternalError(f"Error querying views by text: {e}") from e
