import logging
from typing import List, Optional

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import MonitoringSource, OsintView
from omni_python_library.utils.config import ArangoDBConstant, EntityNameConstant
from omni_python_library.utils.errors import InternalError

logger = logging.getLogger(__name__)


class MonitoringSourceFetcher(ArangoOperator):
    def init(self):
        super().init()

    def get_monitoring_source(self, id: str, owner: str) -> Optional[MonitoringSource]:
        logger.debug(f"Getting monitoring source {id}")
        doc = self._get_from_arango(id, owner=owner, roles=[])
        if doc:
            return MonitoringSource(**doc)
        return None

    def get_monitoring_sources_by_user(self, owner: str, limit: int = 100, offset: int = 0) -> List[MonitoringSource]:
        logger.debug(f"Getting monitoring sources for user: {owner}, limit: {limit}, offset: {offset}")
        query = f"""
            FOR doc IN {EntityNameConstant.MONITORING_SOURCE}
                FILTER doc.owner == @owner
                SORT doc.last_reviewed DESC
                LIMIT @offset, @limit
                RETURN doc
        """
        bind_vars = {"owner": owner, "limit": limit, "offset": offset}
        try:
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
            results = []
            for doc in cursor:
                if isinstance(doc, dict):
                    results.append(MonitoringSource(**doc))
            return results
        except Exception as e:
            raise InternalError("Error getting monitoring sources by user") from e

    def get_views(self, monitoring_source_id: str, owner: str) -> List[OsintView]:
        logger.debug(f"Querying views connected to monitoring source: {monitoring_source_id}")

        query = f"""
            FOR v, e IN 1..1 INBOUND @monitoring_source_id
                FILTER v.owner == @owner
                GRAPH '{ArangoDBConstant.VIEW_GRAPH}'
                RETURN v
        """
        bind_vars = {"owner": owner, "monitoring_source_id": monitoring_source_id}
        try:
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
            results = []
            for doc in cursor:
                if isinstance(doc, dict):
                    results.append(OsintView(**doc))
            return results
        except Exception as e:
            raise InternalError(f"Error getting views for monitoring source {monitoring_source_id}") from e
