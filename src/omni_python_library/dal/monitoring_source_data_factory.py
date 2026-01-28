import logging

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.cacher import Cacher
from omni_python_library.models.monitor import MonitoringSource, MonitoringSourceMainData
from omni_python_library.utils.config_registry import EntityNameConstant

logger = logging.getLogger(__name__)


class MonitoringSourceDataFactory(Cacher):
    def init(self):
        super().init()

    def create_monitoring_source(self, data: MonitoringSourceMainData, user_id: str) -> MonitoringSource:
        logger.debug(f"Creating monitoring source: {data.name} with user_id: {user_id}")

        collection = ArangoDBClient().get_collection(EntityNameConstant.MONITORING_SOURCE)

        doc = data.model_dump(mode="json", by_alias=True, exclude_unset=True)
        doc["user_id"] = user_id

        meta = collection.insert(doc, return_new=True)
        new_doc = meta["new"]

        instance = MonitoringSource(id=new_doc["_id"], key=new_doc["_key"], rev=new_doc["_rev"], **new_doc)

        # Cache the new instance
        self.set(instance.id, instance.model_dump(mode="json", by_alias=True))

        return instance
