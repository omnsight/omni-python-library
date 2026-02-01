import logging
import time
from typing import List, Union

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view.fetcher import ViewDataFetcher
from omni_python_library.models import OsintView, OsintViewMainData, Permissive, RelationMainData, ViewConfig
from omni_python_library.utils import InternalError, NotFoundError

logger = logging.getLogger(__name__)


class ViewDataMutator(ViewDataFetcher):
    def init(self):
        super().init()

    def update_view(self, id: str, data: Union[OsintViewMainData, Permissive]) -> OsintView:
        logger.debug(f"Updating view {id} with data {data}")
        if isinstance(data, OsintViewMainData) and data.configs:
            for config in data.configs:
                self._verify_entities_exist(config.entities)

        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True))
        return OsintView(**updated)

    def add_view_config(self, view_id: str, config: ViewConfig) -> OsintView:
        logger.debug(f"Adding view config {config} to view {view_id}")
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

        try:
            cursor = ArangoDBClient().db.aql.execute(query, bind_vars=bind_vars)
            if cursor.empty():
                raise NotFoundError(f"View {view_id} not found")

            new_doc = cursor.next()
        except NotFoundError:
            raise
        except Exception as e:
            raise InternalError(f"Error adding config to view {view_id}") from e

        # Update cache
        self.set(new_doc["_id"], new_doc)

        return OsintView(**new_doc)

    def connect_entity_to_view(self, view_id: str, entity_id: str) -> OsintView:
        logger.debug(f"Connecting entity {entity_id} to view {view_id}")
        self._verify_entities_exist([entity_id])

        # Fetch view to get owner
        view = self.get_view(view_id)
        if not view:
            raise NotFoundError(f"View {view_id} not found")

        relation_data = RelationMainData(
            name="includes",
            from_id=view_id,
            to_id=entity_id,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )

        OsintDataAccessLayer().create_relation(relation_data, owner=view.owner)

        return view

    def _verify_entities_exist(self, entity_ids: List[str]) -> None:
        if not entity_ids:
            return

        for eid in entity_ids:
            # Using DOCUMENT function to check existence.
            # It returns the document or null if not found.
            query = "RETURN DOCUMENT(@id)"
            try:
                cursor = ArangoDBClient().db.aql.execute(query, bind_vars={"id": eid})
                if cursor.empty() or cursor.next() is None:
                    raise NotFoundError(f"Entity {eid} does not exist in DB")
            except NotFoundError:
                raise
            except Exception as e:
                raise InternalError(f"Error verifying entity existence {eid}") from e
