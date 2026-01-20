from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ViewUI(Enum):
    GEOVISION = "Geovision"
    SPARK_GRAPH = "Sparkle"


class ViewMode(Enum):
    DEFAULT = "default"
    RULER = "ruler"
    COMPARE = "compare"


class EntityView(BaseModel):
    view_id: str = Field(description="Unique identifier for the view")
    view_name: str = Field(description="Name of the view")
    description: str = Field(description="Description of the view")
    entities: List[str] = Field(description="List of entity IDs included in the view")
    relations: List[str] = Field(description="List of relation IDs included in the view")
    selected: List[str] = Field(description="List of selected entity or relation IDs")
    view_ui: ViewUI = Field(description="UI type for the view")
    view_model: ViewMode = Field(description="Mode of the view")
