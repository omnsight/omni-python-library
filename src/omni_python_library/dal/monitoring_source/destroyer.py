import logging

from omni_python_library.dal.base import ArangoOperator

logger = logging.getLogger(__name__)


class MonitoringSourceDataDestroyer(ArangoOperator):
    def init(self):
        super().init()

    def delete_monitoring_source(self, id: str, owner: str) -> None:
        logger.debug(f"Deleting monitoring source: {id}")
        return self._delete_in_arango(id, owner=owner, roles=[])
