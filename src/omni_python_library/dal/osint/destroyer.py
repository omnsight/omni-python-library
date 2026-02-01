import logging

from omni_python_library.dal.base import ArangoOperator

logger = logging.getLogger(__name__)


class OsintDataDestroyer(ArangoOperator):
    def init(self):
        super().init()

    def delete_entity(self, id: str) -> None:
        logger.debug(f"Deleting entity: {id}")
        return self._delete_in_arango(id)

    def delete_relation(self, id: str) -> None:
        logger.debug(f"Deleting relation: {id}")
        return self._delete_in_arango(id)
