from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from omni_python_library.models.common import ArangoData, Permissive


class OsintViewMainData(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100, description="Name of the view")
    description: Optional[str] = Field(default=None, max_length=200, description="Description of the view")
    analysis: Optional[List[Dict[str, Any]]] = Field(
        default=None, max_length=5000, description="Json based analysis report doc"
    )


class OsintView(OsintViewMainData, ArangoData, Permissive):
    def model_dump_main(
        self, mode: Literal["json", "python"] = "python", exclude_unset: bool = False
    ) -> Dict[str, Any]:
        """Dumps the fields from OsintViewMainData into a dictionary."""
        return self.model_dump(
            include=OsintViewMainData.model_fields.keys(),
            mode=mode,
            by_alias=True,
            exclude_unset=exclude_unset,
        )
