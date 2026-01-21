from typing import Dict, Optional

from arango import ArangoClient
from arango.collection import StandardCollection

from omni_python_library.utils.singleton import Singleton


class ArangoDBClient(Singleton):
    def init(
        self,
        host: str = "http://localhost:8529",
        username: str = "root",
        password: str = "",
        db_name: str = "osint_db",
        embedding_dimension: int = 1536,
    ):
        self._host = host
        self._username = username
        self._password = password
        self._db_name = db_name
        self._embedding_dimension = int(embedding_dimension)

        self._client = ArangoClient(hosts=self._host)
        self._db = self._client.db(
            self._db_name,
            username=self._username,
            password=self._password,
        )
        self._collections: Dict[str, StandardCollection] = {}
        self._init_collection("person", indices=[["name"]], vector_index=True)
        self._init_collection("organization", indices=[["name"]], vector_index=True)
        self._init_collection("website", indices=[["url"]], vector_index=True)
        self._init_collection("source", indices=[["url"]], vector_index=True)
        self._init_collection("event", indices=[["happened_at"]], vector_index=True)
        self._init_event_view()

    @property
    def db(self):
        return self._db

    def get_collection(self, name: str):
        col_name = name.lower()
        if col_name in self._collections:
            return self._collections[col_name]
        raise ValueError(f"Collection '{col_name}' is not initialized.")

    def get_edge_collection(self, name: str, from_coll: str, to_coll: str):
        collection_name = f"{from_coll}_{name}_{to_coll}"
        col = self._init_collection(collection_name, edge=True)

        if from_coll == "event" and to_coll == "event":
            self._ensure_in_view("event_view", collection_name)

        return col

    def parse_id(self, id: str):
        col_name = id.split("/")[0]
        key = id.split("/")[-1]
        return col_name, key

    def _init_collection(
        self, name: str, edge: bool = False, indices: Optional[list] = None, vector_index: bool = False
    ):
        if indices is None:
            indices = []
        col_name = name.lower()
        if not self._db.has_collection(col_name):
            self._db.create_collection(col_name, edge=edge)

        col = self._db.collection(col_name)

        for fields in indices:
            col.add_persistent_index(fields=fields)

        if vector_index:
            try:
                col.add_index(
                    {
                        "type": "vector",
                        "fields": ["embedding"],
                        "dimension": self._embedding_dimension,
                        "metric": "cosine",
                    }
                )
            except Exception:
                pass

        self._collections[col_name] = col
        return col

    def _init_event_view(self):
        view_name = "event_view"
        if not self._db.has_view(view_name):
            self._db.create_arangosearch_view(
                view_name, properties={"links": {"event": {"includeAllFields": True}}}
            )
        else:
            self._ensure_in_view(view_name, "event")

    def _ensure_in_view(self, view_name: str, collection_name: str):
        view = self._db.view(view_name)
        props = view.properties()
        links = props.get("links", {})
        if collection_name not in links:
            links[collection_name] = {"includeAllFields": True}
            view.update_properties({"links": links})
