import logging

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.cacher import Cacher

logger = logging.getLogger(__name__)


class ViewDataDestroyer(Cacher):
    def init(self):
        super().init()

    def delete_view(self, id: str) -> bool:
        logger.debug(f"Deleting view: {id}")
        try:
            col_name, key = ArangoDBClient().parse_id(id)

            collection = ArangoDBClient().get_collection(col_name)

            collection.delete({"_key": key})

            # Delete from cache
            self.expel(f"{col_name}/{key}")

            return True
        except Exception:
            logger.exception(f"Error deleting view {id}")
            return False
