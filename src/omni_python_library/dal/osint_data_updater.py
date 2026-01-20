from typing import Any, Dict

from omni_python_library.clients.arangodb import ArangoDBClient
from omni_python_library.dal.cacher import Cacher
from omni_python_library.models.osint import Event, Organization, Person, Relation, Source, Website


class OsintDataUpdater(Cacher):
    def init(self):
        super().init()

    def update_relation(self, id: str, data: Dict[str, Any]) -> Relation:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data)
        return Relation(**final_data)

    def update_event(self, id: str, data: Dict[str, Any]) -> Event:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data)
        return Event(**final_data)

    def update_source(self, id: str, data: Dict[str, Any]) -> Source:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data)
        return Source(**final_data)

    def update_person(self, id: str, data: Dict[str, Any]) -> Person:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data)
        return Person(**final_data)

    def update_organization(self, id: str, data: Dict[str, Any]) -> Organization:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data)
        return Organization(**final_data)

    def update_website(self, id: str, data: Dict[str, Any]) -> Website:
        col_name, key = ArangoDBClient().parse_id(id)
        final_data = self._update(col_name, key, data)
        return Website(**final_data)

    def _update(self, col_name: str, key: str, data: Dict[str, Any]) -> Any:
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
