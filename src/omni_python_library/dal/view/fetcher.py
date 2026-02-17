import logging
from typing import List, Optional, Union

from omni_python_library.dal.base import ArangoOperator
from omni_python_library.dal.osint_data_access_layer import OsintDataAccessLayer
from omni_python_library.models import Event, Organization, OsintView, Person, Relation, Source, Website
from omni_python_library.utils import ArangoDBConstant

logger = logging.getLogger(__name__)


class ViewDataFetcher(ArangoOperator):
    def init(self):
        super().init()

    def get_view(self, id: str, owner: str, roles: List[str]) -> Optional[OsintView]:
        logger.debug(f"Getting view {id}")
        doc = self._get_from_arango(id, owner=owner, roles=roles)
        if doc:
            return OsintView(**doc)
        return None

    def get_entities(
        self, view_id: str, owner: str, roles: List[str]
    ) -> List[Union[Relation, Event, Source, Person, Organization, Website]]:
        logger.debug(f"Querying entities connected to view: {view_id}")

        query = f"""
            FOR v, e IN 1..1 OUTBOUND @view_id
                GRAPH '{ArangoDBConstant.VIEW_GRAPH}'
                FILTER (v.owner == @owner OR LENGTH(INTERSECTION(v.read, @roles)) > 0)
                RETURN v
        """
        bind_vars = {"view_id": view_id, "owner": owner, "roles": roles}
        return OsintDataAccessLayer().query(query, bind_vars=bind_vars)
