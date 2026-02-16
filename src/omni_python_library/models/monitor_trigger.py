from pydantic import BaseModel, Field


class MonitorTrigger(BaseModel):
    """
    Model for monitor trigger.
    """

    user_id: str = Field(description="ID of user who created the trigger")
    language: str = Field(description="The language that workflow generates data in by the trigger")
