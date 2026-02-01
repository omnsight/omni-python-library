import logging
from typing import List

from omni_python_library.dal.base import ArangoOperator

logger = logging.getLogger(__name__)


class ViewDataDestroyer(ArangoOperator):
    def init(self):
        super().init()

    def delete_view(self, id: str, owner: str = None, roles: List[str] = []) -> None:
        logger.debug(f"Deleting view: {id}")
        return self._delete_in_arango(id, owner=owner, roles=roles)
