import logging
from typing import Any, Dict, Union

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.cacher import Cacher
from omni_python_library.models.common import Permissive
from omni_python_library.models.monitor import MonitoringSource, MonitoringSourceMainData

logger = logging.getLogger(__name__)


class MonitoringSourceDataMutator(Cacher):
    def init(self):
        super().init()

    def update_monitoring_source(self, id: str, data: MonitoringSourceMainData) -> MonitoringSource:
        col_name, key = ArangoDBClient().parse_id(id)

        final_data = self._update(col_name, key, data.model_dump(exclude_unset=True))
        return MonitoringSource(**final_data)

    def _update(self, col_name: str, key: str, data: Dict[str, Any]) -> Any:
        logger.debug(f"Internal update: col={col_name}, key={key}")
        try:
            collection = ArangoDBClient().get_collection(col_name)

            # Update in Arango
            update_doc = data.copy()
            update_doc["_key"] = key
            meta = collection.update(update_doc, merge=True, return_new=True)
            updated_doc = meta["new"]
            updated_doc["_id"] = meta["_id"]
            updated_doc["_key"] = meta["_key"]
            updated_doc["_rev"] = meta["_rev"]

            # Update cache
            self.set(updated_doc["_id"], updated_doc)

            return updated_doc
        except Exception:
            logger.exception(f"Error updating monitoring source {col_name}/{key}")
            raise
