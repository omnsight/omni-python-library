import logging
from typing import List

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.base import ArangoOperator

logger = logging.getLogger(__name__)


class ViewDataDestroyer(ArangoOperator):
    def init(self):
        super().init()

    def delete_view(self, id: str, owner: str, roles: List[str]) -> None:
        logger.debug(f"Deleting view: {id}")
        return self._delete_in_arango(id, owner=owner, roles=roles)

    def remove_entity_from_view(self, view_id: str, entity_id: str, owner: str, roles: List[str]) -> None:
        logger.debug(f"Removing entity {entity_id} from view {view_id}")
        src_col_name, _ = ArangoDBClient().parse_id(view_id)
        to_col_name, _ = ArangoDBClient().parse_id(entity_id)
        collection = ArangoDBClient().get_edge_collection(
            name="includes",
            from_coll=src_col_name,
            to_coll=to_col_name,
        )
        query = "FOR r IN @@collection FILTER r._from == @view_id AND r._to == @entity_id RETURN r"
        bind_vars = {"@collection": collection.name, "view_id": view_id, "entity_id": entity_id}
        cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
        if cursor.empty():
            return
        relation = cursor.next()
        return self._delete_in_arango(relation["_id"], owner=owner, roles=roles)
