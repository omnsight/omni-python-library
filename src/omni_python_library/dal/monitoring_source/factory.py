import logging

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import MonitoringSource, MonitoringSourceMainData
from omni_python_library.utils import EntityNameConstant

logger = logging.getLogger(__name__)


class MonitoringSourceDataFactory(ArangoOperator):
    def init(self):
        super().init()

    def create_monitoring_source(self, data: MonitoringSourceMainData, user_id: str) -> MonitoringSource:
        logger.debug(f"Creating monitoring source: {data.name} with user_id: {user_id}")
        doc = self._create_in_arango(
            ArangoDBClient().get_collection(EntityNameConstant.MONITORING_SOURCE),
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            owner=user_id,
        )
        return MonitoringSource(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )
