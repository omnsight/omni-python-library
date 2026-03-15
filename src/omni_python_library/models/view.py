from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from omni_python_library.models.common import ArangoData, Permissive


class OsintViewMainData(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the view")
    description: Optional[str] = Field(default=None, description="Description of the view")
    configs: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of view configurations")


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
