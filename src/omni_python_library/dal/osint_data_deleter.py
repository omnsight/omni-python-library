from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.cacher import Cacher


class OsintDataDeleter(Cacher):
    def init(self):
        super().init()

    def delete_entity(self, id: str) -> bool:
        col_name, key = ArangoDBClient().parse_id(id)
        return self._delete(col_name, key)

    def delete_relation(self, id: str) -> bool:
        col_name, key = ArangoDBClient().parse_id(id)
        return self._delete(col_name, key)

    def _delete(self, col_name: str, key: str) -> bool:
        collection = ArangoDBClient().get_collection(col_name)
        col_name = collection.name

        # Delete from Arango
        try:
            collection.delete({"_key": key})

            # Delete from cache
            self.expel(f"{col_name}/{key}")

            return True
        except Exception:
            return False
