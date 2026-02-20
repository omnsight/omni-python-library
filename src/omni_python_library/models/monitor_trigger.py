from pydantic import BaseModel, Field


class MonitorTriggerMainData(BaseModel):
    """
    Model for monitor trigger.
    """

    language: str = Field(description="The language that workflow generates data in by the trigger")


class MonitorTrigger(MonitorTriggerMainData):
    """
    Model for monitor trigger.
    """

    user_id: str = Field(description="ID of user who created the trigger")
