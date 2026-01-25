import logging
import time
from typing import Any, Dict, List, Union

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.cacher import Cacher
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models.common import Permissive
from omni_python_library.models.osint import RelationMainData
from omni_python_library.models.view import OsintView, OsintViewMainData, ViewConfig

logger = logging.getLogger(__name__)


class ViewDataUpdater(Cacher):
    def init(self):
        super().init()

    def update_view(self, id: str, data: Union[OsintViewMainData, Permissive]) -> OsintView:
        col_name, key = ArangoDBClient().parse_id(id)

        if isinstance(data, OsintViewMainData) and data.configs:
            for config in data.configs:
                self._verify_entities_exist(config.entities)
        elif isinstance(data, dict) and "configs" in data:
            pass

        final_data = self._update(col_name, key, data.model_dump(exclude_unset=True))
        return OsintView(**final_data)

    def add_view_config(self, view_id: str, config: ViewConfig) -> OsintView:
        self._verify_entities_exist(config.entities)

        col_name, key = ArangoDBClient().parse_id(view_id)

        query = f"""
        FOR doc IN {col_name}
            FILTER doc._key == @key
            UPDATE doc WITH {{ configs: APPEND(doc.configs, @config) }} IN {col_name} RETURN NEW
        """

        bind_vars = {
            "key": key,
            "config": config.model_dump(by_alias=True),
        }

        cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
        if cursor.empty():
            raise ValueError(f"View {view_id} not found")

        new_doc = cursor.next()

        # Update cache
        self.set(new_doc["_id"], new_doc)

        return OsintView(**new_doc)

    def connect_entity_to_view(self, view_id: str, entity_id: str) -> OsintView:
        self._verify_entities_exist([entity_id])

        view_col_name, view_key = ArangoDBClient().parse_id(view_id)

        # Fetch view to get owner
        view_collection = ArangoDBClient().get_collection(view_col_name)
        view_doc = view_collection.get({"_key": view_key})
        if not view_doc:
            raise ValueError(f"View {view_id} not found")

        relation_data = RelationMainData(
            name="includes",
            from_id=view_id,
            to_id=entity_id,
            created_at=int(time.time() * 1000)
        )

        OsintDataAccessLayer().create_relation(relation_data, owner=view_doc.get("owner"))

        return OsintView(**view_doc)

    def _verify_entities_exist(self, entity_ids: List[str]):
        if not entity_ids:
            return

        for eid in entity_ids:
            # Using DOCUMENT function to check existence.
            # It returns the document or null if not found.
            query = "RETURN DOCUMENT(@id)"
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars={"id": eid})
            if cursor.empty() or cursor.next() is None:
                raise ValueError(f"Entity {eid} does not exist in DB")

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
            logger.exception(f"Error updating document {col_name}/{key}")
            raise
