from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from omni_python_library.models.common import ArangoData


class MonitoringSourceMainData(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the monitoring source")
    type: Optional[str] = Field(default=None, description="Type of the monitoring source such as 'website', 'news site', 'twitter', 'telegram'")
    url: Optional[str] = Field(default=None, description="URL of the monitoring source")
    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Platform-specific identifiers or handles required to monitor the source via API calls. Examples include a Twitter username handle (e.g., 'elonmusk'), a Telegram channel ID, or a news site URL (e.g., 'https://www.cnn.com').",
    )


class MonitoringSource(ArangoData, MonitoringSourceMainData):
    user_id: str = Field(description="Identify the user the monitoring source belongs to")
