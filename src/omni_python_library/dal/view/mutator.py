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

    def update_view(
        self, id: str, data: Union[OsintViewMainData, Permissive], owner: str = None, roles: List[str] = []
    ) -> OsintView:
        logger.debug(f"Updating view {id} with data {data}")
        if isinstance(data, OsintViewMainData) and data.configs:
            for config in data.configs:
                self._verify_entities_exist(config.entities)

        updated = self._update_in_arango(id, data.model_dump(exclude_unset=True), owner=owner, roles=roles)
        return OsintView(**updated)

    def add_view_config(self, view_id: str, config: ViewConfig, owner: str = None, roles: List[str] = []) -> OsintView:
        logger.debug(f"Adding view config {config} to view {view_id}")
        self._verify_entities_exist(config.entities)

        # Check permissions
        # Fetch document first (checking read permission implicitly)
        doc = self._get_from_arango(view_id, owner=owner, roles=roles)
        if not doc:
            raise NotFoundError(f"View {view_id} not found")

        # Check write permission
        required_roles = doc.get("write", [])
        doc_owner = doc.get("owner")

        # We need to import PermissionDeniedError if not available, but it is imported in dal/base/arango_operator.py
        # Check imports in this file.
        from omni_python_library.utils import PermissionDeniedError

        if not self._check_auth(owner, roles, required_roles, doc_owner):
            raise PermissionDeniedError(f"Permission denied to update view {view_id}. User: {owner}, Roles: {roles}")

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

    def connect_entity_to_view(
        self, view_id: str, entity_id: str, owner: str = None, roles: List[str] = []
    ) -> OsintView:
        logger.debug(f"Connecting entity {entity_id} to view {view_id}")
        self._verify_entities_exist([entity_id])

        # Fetch view to get owner
        # We should use _get_from_arango to check read permissions for the caller
        doc = self._get_from_arango(view_id, owner=owner, roles=roles)
        if not doc:
            raise NotFoundError(f"View {view_id} not found")

        view = OsintView(**doc)

        relation_data = RelationMainData(
            name="includes",
            from_id=view_id,
            to_id=entity_id,
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )

        # Create relation using caller's auth context?
        # Or view owner's context?
        # The original code used `owner=view.owner`.
        # If we want to allow ADMIN to do this, we should pass `roles`.
        # If we use `owner=view.owner`, then we are impersonating the view owner?
        # But `_check_auth` checks if `owner` matches `view.owner`.
        # If we pass `owner=owner` (the caller), then it checks if caller is ADMIN/PRO.
        # Since creating relation requires ADMIN/PRO, passing the caller `owner` and `roles` is better if the caller is ADMIN.
        # But if the caller is just the owner of the view (and not ADMIN/PRO), they should be able to add entities to their view?
        # create_relation requires ADMIN/PRO.
        # So a normal user CANNOT create relations?
        # If so, normal users cannot add entities to views?
        # That seems like a design limitation or intended RBAC.
        # Assuming intended: we pass caller's owner and roles.

        OsintDataAccessLayer().create_relation(relation_data, owner=owner, roles=roles)

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
