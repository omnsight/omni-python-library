from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from omni_python_library.models.common import ArangoData, Permissive


class ViewUI(str, Enum):
    GEOVISION = "Geovision"
    SPARK_GRAPH = "Sparkle"


class ViewMode(str, Enum):
    DEFAULT = "default"
    TIMELINE = "timeline"
    COMPARE = "compare"


class ViewConfig(BaseModel):
    ui: ViewUI = Field(description="UI type for the view")
    mode: ViewMode = Field(description="Mode of the view")
    entities: List[str] = Field(
        description="List of entity ids this view config highlights. For example, compare mode will render these entities in parallel highlighting their differences."
    )


class OsintViewMainData(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the view")
    description: Optional[str] = Field(default=None, description="Description of the view")
    configs: Optional[List[ViewConfig]] = Field(default=None, description="List of view configurations")


class OsintView(OsintViewMainData, ArangoData, Permissive):
    pass
