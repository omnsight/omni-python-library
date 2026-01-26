from typing import Callable, Dict, List, Optional

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
        self._graph_callbacks: List[Callable[[str, str], Optional[str]]] = []

    def init_collection(
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

    def init_graph(self, graph_name: str, callback: Callable[[str, str], Optional[str]]):
        if not self._db.has_graph(graph_name):
            self._db.create_graph(graph_name)
        self._graph_callbacks.append(callback)

    def init_view(self, view_name: str, properties: Dict):
        exists = False
        if hasattr(self._db, "has_view"):
            if self._db.has_view(view_name):
                exists = True
        else:
            # Fallback: check list of views
            try:
                for v in self._db.views():
                    if v["name"] == view_name:
                        exists = True
                        break
            except Exception:
                pass

        if not exists:
            try:
                self._db.create_view(view_name, "arangosearch", properties)
            except Exception:
                # Might fail if it already exists or other issues
                pass

    @property
    def db(self):
        return self._db

    def get_collection(self, name: str):
        col_name = name.lower()
        if col_name in self._collections:
            return self._collections[col_name]

        if self._db.has_collection(col_name):
            self._collections[col_name] = self._db.collection(col_name)
            return self._collections[col_name]
        raise ValueError(f"Collection '{col_name}' is not initialized.")

    def get_edge_collection(self, name: str, from_coll: str, to_coll: str):
        collection_name = f"{from_coll}_{name}_{to_coll}"
        col = self.init_collection(collection_name, edge=True)

        for callback in self._graph_callbacks:
            graph_name = callback(from_coll, to_coll)
            if graph_name:
                self._ensure_in_graph(graph_name, collection_name, from_coll, to_coll)

        return col

    def parse_id(self, id: str):
        col_name = id.split("/")[0]
        key = id.split("/")[-1]
        return col_name, key

    def _ensure_in_graph(self, graph_name: str, edge_collection: str, from_coll: str, to_coll: str):
        graph = self._db.graph(graph_name)
        edge_defs = graph.edge_definitions()

        # Check if edge definition already exists
        exists = False
        for ed in edge_defs:
            if ed["edge_collection"] == edge_collection:
                exists = True
                break

        if not exists:
            graph.create_edge_definition(
                edge_collection=edge_collection, from_vertex_collections=[from_coll], to_vertex_collections=[to_coll]
            )
