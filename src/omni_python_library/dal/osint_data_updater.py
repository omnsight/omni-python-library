import logging
from typing import Any, Dict, Union

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.cacher import Cacher
from omni_python_library.models.common import Permissive
from omni_python_library.models.osint import (
    Event,
    EventMainData,
    Organization,
    OrganizationMainData,
    Person,
    PersonMainData,
    Relation,
    RelationMainData,
    Source,
    SourceMainData,
    Website,
    WebsiteMainData,
)

logger = logging.getLogger(__name__)


class OsintDataUpdater(Cacher):
    def init(self):
        super().init()

    def update_relation(self, id: str, data: Union[RelationMainData, Permissive]) -> Relation:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data.model_dump(exclude_unset=True))
        return Relation(**final_data)

    def update_event(self, id: str, data: Union[EventMainData, Permissive]) -> Event:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data.model_dump(exclude_unset=True))
        return Event(**final_data)

    def update_source(self, id: str, data: Union[SourceMainData, Permissive]) -> Source:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data.model_dump(exclude_unset=True))
        return Source(**final_data)

    def update_person(self, id: str, data: Union[PersonMainData, Permissive]) -> Person:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data.model_dump(exclude_unset=True))
        return Person(**final_data)

    def update_organization(self, id: str, data: Union[OrganizationMainData, Permissive]) -> Organization:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data.model_dump(exclude_unset=True))
        return Organization(**final_data)

    def update_website(self, id: str, data: Union[WebsiteMainData, Permissive]) -> Website:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data.model_dump(exclude_unset=True))
        return Website(**final_data)

    def _update(self, col_name: str, key: str, data: Dict[str, Any]) -> Any:
        logger.debug(f"Internal update: col={col_name}, key={key}")
        try:
            collection = ArangoDBClient().get_collection(col_name)

            # Update in Arango
            # return_new=True gives us the updated document
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
