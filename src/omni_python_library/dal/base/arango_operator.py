import logging
from typing import Any, Dict, List, Optional

from arango.collection import StandardCollection

from omni_python_library.clients import ArangoDBClient
from omni_python_library.dal.base.cacher import Cacher
from omni_python_library.utils import InternalError, NotFoundError, PermissionDeniedError
from omni_python_library.utils.user import UserRole

logger = logging.getLogger(__name__)


class ArangoOperator(Cacher):
    def init(self):
        super().init()

    def _get_from_arango(self, id: str, owner: Optional[str] = None, roles: List[str] = []) -> Optional[Dict[str, Any]]:
        doc = self._raw_fetch(id)
        if not doc:
            return None

        required_roles = doc.get("read", [])
        doc_owner = doc.get("owner")

        if not self._check_auth(owner, roles, required_roles, doc_owner):
            raise PermissionDeniedError(
                f"Permission denied to read document {id}. User: {owner}, Roles: {roles}, Required: {required_roles}, Owner: {doc_owner}"
            )

        return doc

    def _create_in_arango(
        self,
        collection: StandardCollection,
        data: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        owner: Optional[str] = None,
        roles: List[str] = [],
    ) -> Dict[str, Any]:
        if not self._check_auth(owner, roles, [UserRole.ADMIN, UserRole.PRO]):
            raise PermissionDeniedError(f"Only admin and pro users can create documents. User: {owner}, Roles: {roles}")

        if embedding:
            data["embedding"] = embedding
        if owner:
            data["owner"] = owner

        try:
            meta = collection.insert(data, return_new=True)
            new_doc = meta["new"]
            self.set(new_doc["_id"], new_doc)
            return new_doc
        except Exception as e:
            raise InternalError(f"Error creating document in {collection.name}") from e

    def _update_in_arango(
        self, id: str, data: Dict[str, Any], owner: Optional[str] = None, roles: List[str] = []
    ) -> Dict[str, Any]:
        doc = self._raw_fetch(id)
        if not doc:
            raise NotFoundError(f"Document {id} not found")

        required_roles = doc.get("write", [])
        doc_owner = doc.get("owner")

        if not self._check_auth(owner, roles, required_roles, doc_owner):
            raise PermissionDeniedError(
                f"Permission denied to update document {id}. User: {owner}, Roles: {roles}, Required: {required_roles}, Owner: {doc_owner}"
            )

        try:
            col_name, key = ArangoDBClient().parse_id(id)
            collection = ArangoDBClient().get_collection(col_name)

            data["_key"] = key
            meta = collection.update(data, merge=True, return_new=True)
            doc = meta["new"]
            doc["_id"] = meta["_id"]
            doc["_key"] = meta["_key"]
            doc["_rev"] = meta["_rev"]
            self.set(id, doc)
            return doc
        except Exception as e:
            raise InternalError(f"Error updating document {id}") from e

    def _delete_in_arango(self, id: str, owner: Optional[str] = None) -> bool:
        doc = self._raw_fetch(id)
        if not doc:
            raise NotFoundError(f"Document {id} not found")

        doc_owner = doc.get("owner")
        # Check if owner matches
        if not self._check_auth(owner, [], [], doc_owner):
            raise PermissionDeniedError(f"Permission denied to delete document {id}. User: {owner}, Owner: {doc_owner}")

        try:
            col_name, key = ArangoDBClient().parse_id(id)
            collection = ArangoDBClient().get_collection(col_name)
            collection.delete({"_key": key})
            self.expel(id)
            return True
        except Exception as e:
            raise InternalError(f"Error deleting document {id}") from e

    def _raw_fetch(self, id: str) -> Optional[Dict[str, Any]]:
        cached_data = super().get(id)
        if cached_data:
            return cached_data

        try:
            col_name, key = ArangoDBClient().parse_id(id)
            collection = ArangoDBClient().get_collection(col_name)
            doc = collection.get({"_key": key})
            if doc:
                self.set(id, doc)
                return doc
        except Exception as e:
            raise InternalError(f"Error fetching generic document {id}") from e
        return None

    def _check_auth(
        self, user_id: Optional[str], user_roles: List[str], required_roles: List[str], doc_owner: Optional[str] = None
    ) -> bool:
        if user_id and doc_owner and user_id == doc_owner:
            return True
        if not required_roles:
            return False
        return bool(set(required_roles) & set(user_roles))
