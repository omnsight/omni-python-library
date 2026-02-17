import logging
from datetime import datetime
from typing import List

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import MonitoringSource, MonitoringSourceMainData
from omni_python_library.utils import EntityNameConstant

logger = logging.getLogger(__name__)


class MonitoringSourceDataFactory(ArangoOperator):
    def init(self):
        super().init()

    def create_monitoring_source(
        self, data: MonitoringSourceMainData, owner: str, roles: List[str]
    ) -> MonitoringSource:
        logger.debug(f"Creating monitoring source: {data.name} with owner: {owner}")
        data.last_reviewed = int(datetime.now().timestamp())
        doc = self._create_in_arango(
            ArangoDBClient().get_collection(EntityNameConstant.MONITORING_SOURCE),
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            owner=owner,
            roles=roles,
        )
        return MonitoringSource(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )
