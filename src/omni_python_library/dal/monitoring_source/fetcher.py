import logging
from typing import List, Optional

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import MonitoringSource
from omni_python_library.utils import EntityNameConstant, InternalError

logger = logging.getLogger(__name__)


class MonitoringSourceFetcher(ArangoOperator):
    def init(self):
        super().init()

    def get_monitoring_source(self, id: str) -> Optional[MonitoringSource]:
        logger.debug(f"Getting monitoring source {id}")
        doc = self._get_from_arango(id)
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
        except Exception as e:
            raise InternalError("Error getting monitoring sources by user") from e
