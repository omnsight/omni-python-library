from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from omni_python_library.models.common import ArangoData


class SourceType(str, Enum):
    WEBSITE = "website"
    TWITTER = "twitter"
    TELEGRAM = "telegram"


class MonitoringSourceMainData(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the monitoring source")
    type: Optional[SourceType] = Field(default=None, description="Type of the monitoring source such as 'website', 'twitter', 'telegram'")
    url: Optional[str] = Field(default=None, description="URL of the monitoring source")
    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Platform-specific identifiers or handles required to monitor the source via API calls. Examples include a Twitter user id or a Telegram channel ID.",
    )


class MonitoringSource(ArangoData, MonitoringSourceMainData):
    user_id: str = Field(description="Identify the user the monitoring source belongs to")
