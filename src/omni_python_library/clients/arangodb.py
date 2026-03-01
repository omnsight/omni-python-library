from typing import Callable, Dict, List, Optional, Tuple

from arango import ArangoClient
from arango.collection import StandardCollection

from omni_python_library.utils import Singleton
from omni_python_library.utils.errors import NotFoundError


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

        # Connect to "_system" database to create the target database if it doesn't exist.
        sys_db = self._client.db("_system", username=self._username, password=self._password)
        if not sys_db.has_database(self._db_name):
            sys_db.create_database(self._db_name)

        self._db = self._client.db(
            self._db_name,
            username=self._username,
            password=self._password,
        )
        self._collections: Dict[str, StandardCollection] = {}
        self._graph_callbacks: List[Callable[[str, str], Optional[str]]] = []

    def init_collection(
        self, name: str, edge: bool = False, indices: List[Tuple[str, str]] = [], vector_index: bool = False
    ) -> StandardCollection:
        col_name = name.lower()
        if not self._db.has_collection(col_name):
            self._db.create_collection(col_name, edge=edge)

        col = self._db.collection(col_name)

        for type, index in indices:
            col.add_index(
                {
                    "type": type,
                    "fields": [index],
                }
            )

        if vector_index:
            try:
                col.add_index(
                    {
                        "type": "vector",
                        "fields": ["embedding"],
                        "params": {
                            "dimension": self._embedding_dimension,
                            "metric": "cosine",
                            "nLists": 100,
                            "defaultNProbe": 10,
                        },
                    }
                )
            except Exception as e:
                # ArangoDB 3.12+ requires data to exist for vector index creation.
                # If the collection is empty, this will fail. We log and continue.
                print(f"Warning: Failed to create vector index on '{col_name}': {e}")

        self._collections[col_name] = col
        return col

    def init_graph(self, graph_name: str, callback: Callable[[str, str], Optional[str]]) -> None:
        if not self._db.has_graph(graph_name):
            self._db.create_graph(graph_name)
        self._graph_callbacks.append(callback)

    def init_view(self, view_name: str, properties: Dict) -> None:
        exists = False
        for v in self._db.views():
            if v["name"] == view_name:
                exists = True
                break

        if not exists:
            self._db.create_view(view_name, "arangosearch", properties)

    @property
    def db(self):
        return self._db

    def get_collection(self, name: str) -> StandardCollection:
        col_name = name.lower()
        if col_name in self._collections:
            return self._collections[col_name]

        if self._db.has_collection(col_name):
            self._collections[col_name] = self._db.collection(col_name)
            return self._collections[col_name]

        raise NotFoundError(f"Collection '{col_name}' is not found.")

    def get_edge_collection(self, name: str, from_coll: str, to_coll: str) -> StandardCollection:
        col_name = f"{from_coll}_{name}_{to_coll}"
        if col_name in self._collections:
            return self._collections[col_name]

        col = self.init_collection(col_name, edge=True)

        for callback in self._graph_callbacks:
            graph_name = callback(from_coll, to_coll)
            if graph_name:
                self._ensure_in_graph(graph_name, col_name, from_coll, to_coll)

        return col

    def parse_id(self, id: str) -> Tuple[str, str]:
        col_name = id.split("/")[0]
        key = id.split("/")[-1]
        return col_name, key

    def _ensure_in_graph(self, graph_name: str, edge_collection: str, from_coll: str, to_coll: str) -> None:
        graph = self._db.graph(graph_name)
        edge_defs = graph.edge_definitions()

        exists = False
        for ed in edge_defs:
            if ed["edge_collection"] == edge_collection:
                exists = True
                break

        if not exists:
            graph.create_edge_definition(
                edge_collection=edge_collection, from_vertex_collections=[from_coll], to_vertex_collections=[to_coll]
            )
