from enum import Enum
from typing import List
from pydantic import Field
from pydantic import BaseModel
from omni_python_library.models.common import ArangoData, Permissive


class ViewUI(Enum):
    GEOVISION = "Geovision"
    SPARK_GRAPH = "Sparkle"


class ViewMode(Enum):
    DEFAULT = "default"
    TIMELINE = "timeline"
    COMPARE = "compare"


class ViewConfig(BaseModel):
    ui: ViewUI = Field(description="UI type for the view")
    mode: ViewMode = Field(description="Mode of the view")
    entities: List[str] = Field(description="List of entity ids this view config highlights. For example, compare mode will render these entities in parallel highlighting their differences.")


class OsintViewMainData(BaseModel):
    name: str = Field(description="Name of the view")
    description: str = Field(description="Description of the view") 
    configs: List[ViewConfig] = Field(description="List of view configurations")


class OsintView(OsintViewMainData, ArangoData, Permissive):
    pass
