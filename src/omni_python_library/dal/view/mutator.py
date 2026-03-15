import logging
from typing import List, Union

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.dal.view.fetcher import ViewDataFetcher
from omni_python_library.models import OsintView, OsintViewMainData, Permissive, RelationMainData
from omni_python_library.utils.errors import InternalError, NotFoundError

logger = logging.getLogger(__name__)


class ViewDataMutator(ViewDataFetcher):
    def init(self):
        super().init()

    def update_view(
        self, id: str, data: Union[OsintViewMainData, Permissive], owner: str, roles: List[str]
    ) -> OsintView:
        logger.debug(f"Updating view {id} with data {data}")

        updated = self._update_in_arango(
            id, data.model_dump(mode="json", by_alias=True, exclude_unset=True), owner=owner, roles=roles
        )
        return OsintView(**updated)

    def connect_entity_to_view(self, view_id: str, entity_id: str, owner: str, roles: List[str]) -> OsintView:
        logger.debug(f"Connecting entity {entity_id} to view {view_id}")
        self._verify_entities_exist([entity_id])

        # Fetch view to get owner
        doc = self._get_from_arango(view_id, owner=owner, roles=roles)
        if not doc:
            raise NotFoundError(f"View {view_id} not found")

        view = OsintView(**doc)

        relation_data = RelationMainData(
            name="includes",
            from_id=view_id,
            to_id=entity_id,
        )

        OsintDataAccessLayer().create_relation(relation_data, owner=owner, roles=roles)

        return view

    def _verify_entities_exist(self, entity_ids: List[str]) -> None:
        if not entity_ids:
            return

        for eid in entity_ids:
            query = "RETURN DOCUMENT(@id)"
            try:
                cursor = ArangoDBClient().db.aql.execute(query, bind_vars={"id": eid})
                if cursor.empty() or cursor.next() is None:
                    raise NotFoundError(f"Entity {eid} does not exist in DB")
            except NotFoundError:
                raise
            except Exception as e:
                raise InternalError(f"Error verifying entity existence {eid}") from e
