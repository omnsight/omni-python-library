import logging
import os
from typing import Dict

from omni_python_library.utils.singleton import Singleton

logger = logging.getLogger(__name__)


class EntityNameConstant:
    EVENT = "event"
    PERSON = "person"
    ORGANIZATION = "organization"
    WEBSITE = "website"
    SOURCE = "source"
    RELATION = "relation"
    VIEW = "osintview"
    MONITORING_SOURCE = "monitoringsource"


class ArangoDBConstant:
    EVENT_RELATED_GRAPH = "event_related_graph"
    EVENT_GRAPH = "event_graph"
    VIEW_GRAPH = "osint_view_graph"


class LLMConstant:
    EMBEDDING = "embedding"


class ConfigRegistry(Singleton):
    def init(self, root_path: str):
        self._configs: Dict[str, str] = {}
        self.root_path = root_path

    def get(self, key: str) -> str:
        stage = os.getenv("stage")
        if stage == "local":
            val = os.getenv(key)
            if val is None:
                logger.warning(f"Environment variable {key} not found in local stage")
                return ""
            return val
        else:
            file_path = os.path.join(self.root_path, key)
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    return f.read().strip()

            val = os.getenv(key)
            if val is None:
                raise Exception(f"Config key {key} not found in both file and env var")
            return val
