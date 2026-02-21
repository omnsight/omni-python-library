import logging
from typing import List

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.base import ArangoOperator
from omni_python_library.models import OsintView, OsintViewMainData
from omni_python_library.utils.config import EntityNameConstant

logger = logging.getLogger(__name__)


class ViewDataFactory(ArangoOperator):
    def init(self):
        super().init()

    def create_view(self, data: OsintViewMainData, owner: str, roles: List[str]) -> OsintView:
        logger.debug(f"Creating view: {data.name} with owner: {owner}")
        doc = self._create_in_arango(
            ArangoDBClient().get_collection(EntityNameConstant.VIEW),
            data.model_dump(mode="json", by_alias=True, exclude_unset=True),
            owner=owner,
            roles=roles,
        )
        return OsintView(
            id=doc["_id"],
            key=doc["_key"],
            rev=doc["_rev"],
            **doc,
        )
