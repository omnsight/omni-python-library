from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

from omni_python_library.models.common import ArangoData


class SourceType(str, Enum):
    WEBSITE = "website"
    TWITTER = "twitter"
    TELEGRAM = "telegram"


class MonitoringSourceMainData(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the monitoring source")
    description: Optional[str] = Field(
        default=None, description="Describe what kind of information the source focuses on"
    )
    type: Optional[SourceType] = Field(
        default=None, description="Type of the monitoring source such as 'website', 'twitter', 'telegram'"
    )
    url: Optional[str] = Field(default=None, description="URL of the monitoring source")
    reliability: Optional[float] = Field(
        default=None, description="Reliability score of the monitoring source, ranging from 0 to 100"
    )
    last_reviewed: Optional[int] = Field(
        default=None, description="The last time the source was reviewed, in epoch time"
    )
    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Platform-specific identifiers or handles required to monitor the source via API calls. Examples include a Twitter user id or a Telegram channel ID.",
    )


class MonitoringSource(ArangoData, MonitoringSourceMainData):
    owner: str = Field(description="Identify the user the monitoring source belongs to")

    def model_dump_main(
        self, mode: Literal["json", "python"] = "python", exclude_unset: bool = False
    ) -> Dict[str, Any]:
        """Dumps the fields from MonitoringSourceMainData into a dictionary."""
        return self.model_dump(
            include=MonitoringSourceMainData.model_fields.keys(),
            mode=mode,
            by_alias=True,
            exclude_unset=exclude_unset,
        )
