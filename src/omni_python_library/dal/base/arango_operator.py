import logging
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Union

from arango.collection import StandardCollection

from omni_python_library.clients import PENDING_UPDATES, ArangoDBClient, OpenAIClient
from omni_python_library.dal.base.cacher import Cacher
from omni_python_library.utils import InternalError, LLMConstant, NotFoundError, PermissionDeniedError, UserRole

logger = logging.getLogger(__name__)


class ArangoOperator(Cacher):
    def init(self):
        super().init()

    def _get_from_arango(
        self, id: str, owner: str, roles: List[str], in_pending: bool = False
    ) -> Optional[Dict[str, Any]]:
        doc = self._raw_fetch(id)
        if not doc:
            return None

        required_roles = doc.get("read", [])
        doc_owner = doc.get("owner")

        if not self._check_auth(owner, roles, required_roles, doc_owner):
            raise PermissionDeniedError(
                f"Permission denied to read document {id}. User: {owner}, Roles: {roles}, Required: {required_roles}, Owner: {doc_owner}"
            )

        pending = self.get(id, db=PENDING_UPDATES)
        if pending and in_pending:
            return {**doc, **pending}
        else:
            return doc

    def _create_in_arango(
        self,
        collection: StandardCollection,
        data: Dict[str, Any],
        owner: str,
        roles: List[str],
        embedding_fields: List[str] = [],
        pending_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self._check_auth(owner, roles, [UserRole.ADMIN, UserRole.PRO]):
            raise PermissionDeniedError(f"Only admin and pro users can create documents. User: {owner}, Roles: {roles}")

        if embedding_fields:
            embedding_text = " ".join(str(data.get(f, "")) for f in embedding_fields)
            embedding = self.generate_embedding(embedding_text)
            if embedding:
                data["embedding"] = embedding
        if owner:
            data["owner"] = owner

        try:
            meta = collection.insert(data, return_new=True)
            new_doc = meta["new"]
            self.set(new_doc["_id"], new_doc)
            if pending_data:
                self.set(new_doc["_id"], pending_data, db=PENDING_UPDATES)
            return new_doc
        except Exception as e:
            raise InternalError(f"Error creating document in {collection.name}") from e

    def _update_in_arango(
        self,
        id: str,
        data: Dict[str, Any],
        owner: str,
        roles: List[str],
        embedding_fields: List[str] = [],
        in_pending: bool = False,
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

        if in_pending:
            self.set(id, data, db=PENDING_UPDATES)
            return {**doc, **data}

        pending = self.get(id, db=PENDING_UPDATES)
        if pending:
            data = {**pending, **data}

        if embedding_fields:
            fields_to_compare = [field for field in embedding_fields if field in data]
            if fields_to_compare:
                original_text_parts = [str(doc.get(field, "")) for field in fields_to_compare]
                new_text_parts = [str(data.get(field, "")) for field in fields_to_compare]

                original_embedding_text = " ".join(original_text_parts)
                new_embedding_text = " ".join(new_text_parts)

                if SequenceMatcher(None, original_embedding_text, new_embedding_text).ratio() < 0.9:
                    embedding_text = " ".join(str(data.get(f, doc.get(f, ""))) for f in embedding_fields)
                    embedding = self.generate_embedding(embedding_text)
                    if embedding:
                        data["embedding"] = embedding

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

    def _delete_in_arango(self, id: str, owner: str, roles: List[str]) -> bool:
        doc = self._raw_fetch(id)
        if not doc:
            raise NotFoundError(f"Document {id} not found")

        doc_owner = doc.get("owner")
        # Check if owner matches
        if not self._check_auth(owner, roles, [], doc_owner):
            raise PermissionDeniedError(f"Permission denied to delete document {id}. User: {owner}, Owner: {doc_owner}")

        try:
            col_name, key = ArangoDBClient().parse_id(id)
            collection = ArangoDBClient().get_collection(col_name)
            collection.delete({"_key": key})
            self.expel(id)
            self.expel(id, db=PENDING_UPDATES)
            return True
        except Exception as e:
            raise InternalError(f"Error deleting document {id}") from e

    def _raw_fetch(self, id: str) -> Optional[Dict[str, Any]]:
        cached_data = self.get(id)
        if cached_data:
            return cached_data

        try:
            col_name, key = ArangoDBClient().parse_id(id)
            collection = ArangoDBClient().get_collection(col_name)
            doc = collection.get({"_key": key})
            if doc:
                self.set(id, doc)
                return doc
        except NotFoundError:
            raise
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

    def generate_embedding(self, text: Optional[str]) -> Union[List[float] | None]:
        client_tuple = OpenAIClient().get_client(LLMConstant.EMBEDDING)
        if not client_tuple or not text:
            return None

        client, model = client_tuple
        if not client:
            return None

        try:
            response = client.embeddings.create(input=text, model=model)
            return response.data[0].embedding
        except Exception as e:
            raise InternalError("Error generating embedding") from e
