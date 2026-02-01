import logging
from typing import List

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.view import ViewDataDestroyer, ViewDataFactory, ViewDataMutator
from omni_python_library.models import OsintView
from omni_python_library.utils import ArangoDBConstant, EntityNameConstant, InternalError

logger = logging.getLogger(__name__)


class ViewDataAccessLayer(ViewDataFactory, ViewDataMutator, ViewDataDestroyer):
    def __init__(self):
        super().__init__()
        ArangoDBClient().init_collection(
            EntityNameConstant.VIEW,
            indices=[("inverted", "name"), ("inverted", "description")],
            vector_index=False,
        )
        ArangoDBClient().init_graph(
            ArangoDBConstant.VIEW_GRAPH,
            lambda from_coll, to_coll: ArangoDBConstant.VIEW_GRAPH if from_coll == EntityNameConstant.VIEW else None,
        )

    def query_views(self, text: str, owner: str, lang: str = "en", limit: int = 100) -> List[OsintView]:
        logger.debug(f"Querying views by text: {text} and owner: {owner}")

        query = f"""
            LET terms = TOKENS(@text, "text_{lang}")
            FOR doc IN {EntityNameConstant.VIEW}
                SEARCH ANALYZER(
                    MIN_MATCH(
                        doc.name IN terms,
                        doc.description IN terms,
                        LENGTH(terms)
                    ),
                    "text_{lang}"
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
        except Exception as e:
            raise InternalError("Error querying views by text") from e
