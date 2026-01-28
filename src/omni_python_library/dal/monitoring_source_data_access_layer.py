import logging
from typing import Any, Dict, List, Optional

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.monitoring_source_data_destroyer import MonitoringSourceDataDestroyer
from omni_python_library.dal.monitoring_source_data_factory import MonitoringSourceDataFactory
from omni_python_library.dal.monitoring_source_data_mutator import MonitoringSourceDataMutator
from omni_python_library.models.monitor import MonitoringSource
from omni_python_library.utils.config_registry import EntityNameConstant

logger = logging.getLogger(__name__)


class MonitoringSourceDataAccessLayer(
    MonitoringSourceDataFactory, MonitoringSourceDataMutator, MonitoringSourceDataDestroyer
):
    def __init__(self):
        super().__init__()
        client = ArangoDBClient()
        client.init_collection(
            EntityNameConstant.MONITORING_SOURCE,
            indices=[("inverted", "name"), ("inverted", "type")],
            vector_index=False,
        )

    def get_monitoring_source(self, id: str) -> Optional[MonitoringSource]:
        logger.debug(f"Getting monitoring source {id}")
        doc = self._get_generic(id)
        if doc:
            return MonitoringSource(**doc)
        return None

    def get_monitoring_sources_by_user(self, user_id: str) -> List[MonitoringSource]:
        logger.debug(f"Getting monitoring sources for user: {user_id}")
        query = f"""
            FOR doc IN {EntityNameConstant.MONITORING_SOURCE}
                FILTER doc.user_id == @user_id
                RETURN doc
        """
        bind_vars = {"user_id": user_id}
        try:
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
            results = []
            for doc in cursor:
                if isinstance(doc, dict):
                    results.append(MonitoringSource(**doc))
            return results
        except Exception:
            logger.exception("Error getting monitoring sources by user")
            raise

    def query_monitoring_sources(self, text: str, user_id: str, limit: int = 100) -> List[MonitoringSource]:
        logger.debug(f"Querying monitoring sources by text: {text} and user_id: {user_id}")

        query = f"""
            LET terms = TOKENS(@text, "text_en")
            FOR doc IN {EntityNameConstant.MONITORING_SOURCE}
                SEARCH ANALYZER(
                    MIN_MATCH(
                        doc.name IN terms,
                        doc.type IN terms,
                        LENGTH(terms)
                    ),
                    "text_en"
                )
                FILTER doc.user_id == @user_id
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
        except Exception:
            logger.exception("Error querying monitoring sources by text")
            raise

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
