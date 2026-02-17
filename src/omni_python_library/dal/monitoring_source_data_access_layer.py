import logging
from typing import List

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.monitoring_source import (
    MonitoringSourceDataDestroyer,
    MonitoringSourceDataFactory,
    MonitoringSourceDataMutator,
)
from omni_python_library.models import MonitoringSource
from omni_python_library.utils import EntityNameConstant, InternalError

logger = logging.getLogger(__name__)


class MonitoringSourceDataAccessLayer(
    MonitoringSourceDataFactory, MonitoringSourceDataMutator, MonitoringSourceDataDestroyer
):
    def init(self):
        super().init()
        ArangoDBClient().init_collection(
            EntityNameConstant.MONITORING_SOURCE,
            indices=[],
            vector_index=False,
        )
        ArangoDBClient().init_view(
            "monitoringsource_view",
            {
                "links": {
                    EntityNameConstant.MONITORING_SOURCE: {
                        "analyzers": ["text_en", "identity"],
                        "includeAllFields": True,
                    }
                }
            },
        )

    def query_monitoring_sources(self, text: str, user_id: str, limit: int = 100) -> List[MonitoringSource]:
        logger.debug(f"Querying monitoring sources by text: {text} and user_id: {user_id}")

        query = f"""
            LET terms = TOKENS(@text, "text_en")
            FOR doc IN monitoringsource_view
                SEARCH ANALYZER(
                    MIN_MATCH(
                        doc.name IN terms,
                        doc.type IN terms,
                        LENGTH(terms)
                    ),
                    "text_en"
                )
                FILTER doc.owner == @user_id
                LIMIT @limit
                RETURN doc
        """

        bind_vars = {"text": text, "user_id": user_id, "limit": limit}
        try:
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
            results = []
            for doc in cursor:
                if isinstance(doc, dict):
                    results.append(MonitoringSource(**doc))
            return results
        except Exception as e:
            raise InternalError(f"Error querying monitoring sources by text: {e}") from e
