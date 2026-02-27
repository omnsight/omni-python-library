from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from omni_python_library.models.common import ArangoData, LocationData, Permissive


# Relation
class RelationMainData(BaseModel):
    name: Optional[str] = Field(
        default=None, description="Name of the relation used in database key (must be ascii letters)"
    )
    confidence: Optional[int] = Field(default=None, description="Confidence score")
    label: Optional[str] = Field(
        default=None, description="Label name of the relation (can be any language) to display"
    )
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")

    # Edges specific fields
    from_id: Optional[str] = Field(default=None, alias="_from", description="Source document ID")
    to_id: Optional[str] = Field(default=None, alias="_to", description="Target document ID")

    model_config = ConfigDict(populate_by_name=True)


class Relation(ArangoData, Permissive, RelationMainData):
    """
    Represents a relationship between two entities.
    """

    def model_dump_main(
        self, mode: Literal["json", "python"] = "python", exclude_unset: bool = False
    ) -> Dict[str, Any]:
        """Dumps the fields from RelationMainData into a dictionary."""
        return self.model_dump(
            include=RelationMainData.model_fields.keys(),
            mode=mode,
            by_alias=True,
            exclude_unset=exclude_unset,
        )


# Event
class EventMainData(BaseModel):
    type: Optional[str] = Field(default=None, description="Type of event")
    location: Optional[LocationData] = Field(default=None, description="Location of the event")
    title: Optional[str] = Field(default=None, description="Title of the event. Keep it short and clear.")
    description: Optional[str] = Field(
        default=None, description="Brief description of the event. Keep it short and clear."
    )
    happened_at: Optional[int] = Field(default=None, description="Timestamp when the event happened")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Event(ArangoData, Permissive, EventMainData):
    """
    Represents an event.
    """

    def model_dump_main(
        self, mode: Literal["json", "python"] = "python", exclude_unset: bool = False
    ) -> Dict[str, Any]:
        """Dumps the fields from EventMainData into a dictionary."""
        return self.model_dump(
            include=EventMainData.model_fields.keys(),
            mode=mode,
            by_alias=True,
            exclude_unset=exclude_unset,
        )


# Source
class SourceMainData(BaseModel):
    type: Optional[str] = Field(default=None, description="Type of source")
    url: Optional[str] = Field(default=None, description="URL")
    name: Optional[str] = Field(default=None, description="Name of the source")
    title: Optional[str] = Field(default=None, description="Title of the source. Keep it short and clear.")
    description: Optional[str] = Field(
        default=None, description="Brief description of the source. Keep it short and clear."
    )
    reliability: Optional[int] = Field(default=None, description="Reliability score")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Source(ArangoData, Permissive, SourceMainData):
    """
    Represents a source of information.
    """

    def model_dump_main(
        self, mode: Literal["json", "python"] = "python", exclude_unset: bool = False
    ) -> Dict[str, Any]:
        """Dumps the fields from SourceMainData into a dictionary."""
        return self.model_dump(
            include=SourceMainData.model_fields.keys(),
            mode=mode,
            by_alias=True,
            exclude_unset=exclude_unset,
        )


# Person
class PersonMainData(BaseModel):
    role: Optional[str] = Field(default=None, description="Role")
    name: Optional[str] = Field(default=None, description="Name")
    nationality: Optional[str] = Field(default=None, description="Nationality")
    birth_date: Optional[int] = Field(default=None, description="Person's birth date (timestamp)")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    aliases: Optional[List[str]] = Field(default=None, description="Aliases")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Person(ArangoData, Permissive, PersonMainData):
    """
    Represents a person.
    """

    def model_dump_main(
        self, mode: Literal["json", "python"] = "python", exclude_unset: bool = False
    ) -> Dict[str, Any]:
        """Dumps the fields from PersonMainData into a dictionary."""
        return self.model_dump(
            include=PersonMainData.model_fields.keys(),
            mode=mode,
            by_alias=True,
            exclude_unset=exclude_unset,
        )


# Organization
class OrganizationMainData(BaseModel):
    type: Optional[str] = Field(default=None, description="Type of organization")
    name: Optional[str] = Field(default=None, description="Name of the organization")
    founded_at: Optional[int] = Field(default=None, description="When organization is founded (timestamp)")
    discovered_at: Optional[int] = Field(default=None, description="When organization is discovered (timestamp)")
    last_visited: Optional[int] = Field(default=None, description="When organization is last visited (timestamp)")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Organization(ArangoData, Permissive, OrganizationMainData):
    """
    Represents an organization.
    """

    def model_dump_main(
        self, mode: Literal["json", "python"] = "python", exclude_unset: bool = False
    ) -> Dict[str, Any]:
        """Dumps the fields from OrganizationMainData into a dictionary."""
        return self.model_dump(
            include=OrganizationMainData.model_fields.keys(),
            mode=mode,
            by_alias=True,
            exclude_unset=exclude_unset,
        )


# Website
class WebsiteMainData(BaseModel):
    url: Optional[str] = Field(default=None, description="URL")
    title: Optional[str] = Field(default=None, description="Title of the website. Keep it short and clear.")
    description: Optional[str] = Field(
        default=None, description="Brief description of the website. Keep it short and clear."
    )
    founded_at: Optional[int] = Field(default=None, description="When website is founded (timestamp)")
    discovered_at: Optional[int] = Field(default=None, description="When website is discovered (timestamp)")
    last_visited: Optional[int] = Field(default=None, description="When website is last visited (timestamp)")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Website(ArangoData, Permissive, WebsiteMainData):
    """
    Represents a website.
    """

    def model_dump_main(
        self, mode: Literal["json", "python"] = "python", exclude_unset: bool = False
    ) -> Dict[str, Any]:
        """Dumps the fields from WebsiteMainData into a dictionary."""
        return self.model_dump(
            include=WebsiteMainData.model_fields.keys(),
            mode=mode,
            by_alias=True,
            exclude_unset=exclude_unset,
        )
