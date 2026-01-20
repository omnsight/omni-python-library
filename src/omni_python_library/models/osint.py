from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from omni_python_library.models.common import ArangoData, LocationData, Permissive


# Relation
class RelationMainData(BaseModel):
    name: str = Field(description="Name of the relation")
    confidence: int = Field(description="Confidence score")
    label: str = Field(description="Label")
    created_at: int = Field(description="Creation timestamp")
    updated_at: int = Field(description="Update timestamp")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")

    # Edges specific fields
    from_id: str = Field(alias="_from", description="Source document ID")
    to_id: str = Field(alias="_to", description="Target document ID")

    model_config = ConfigDict(populate_by_name=True)


class Relation(ArangoData, Permissive, RelationMainData):
    """
    Represents a relationship between two entities.
    """

    pass


# Event
class EventMainData(BaseModel):
    type: str = Field(description="Type of event")
    location: LocationData = Field(description="Location of the event")
    title: str = Field(description="Title")
    description: str = Field(description="Description")
    happened_at: int = Field(description="Timestamp when the event happened")
    updated_at: int = Field(description="Update timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")


class Event(ArangoData, Permissive, EventMainData):
    """
    Represents an event.
    """

    pass


# Source
class SourceMainData(BaseModel):
    type: str = Field(description="Type of source")
    url: str = Field(description="URL")
    name: str = Field(description="Name")
    title: str = Field(description="Title")
    description: str = Field(description="Description")
    reliability: int = Field(description="Reliability score")
    created_at: int = Field(description="Creation timestamp")
    updated_at: int = Field(description="Update timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")


class Source(ArangoData, Permissive, SourceMainData):
    """
    Represents a source of information.
    """

    pass


# Person
class PersonMainData(BaseModel):
    role: str = Field(description="Role")
    name: str = Field(description="Name")
    nationality: str = Field(description="Nationality")
    birth_date: int = Field(description="Birth date timestamp")
    updated_at: int = Field(description="Update timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags")
    aliases: List[str] = Field(default_factory=list, description="Aliases")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")


class Person(ArangoData, Permissive, PersonMainData):
    """
    Represents a person.
    """

    pass


# Organization
class OrganizationMainData(BaseModel):
    type: str = Field(description="Type of organization")
    name: str = Field(description="Name")
    founded_at: int = Field(description="Founded timestamp")
    discovered_at: int = Field(description="Discovered timestamp")
    last_visited: int = Field(description="Last visited timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")


class Organization(ArangoData, Permissive, OrganizationMainData):
    """
    Represents an organization.
    """

    pass


# Website
class WebsiteMainData(BaseModel):
    url: str = Field(description="URL")
    title: str = Field(description="Title")
    description: str = Field(description="Description")
    founded_at: int = Field(description="Founded timestamp")
    discovered_at: int = Field(description="Discovered timestamp")
    last_visited: int = Field(description="Last visited timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")


class Website(ArangoData, Permissive, WebsiteMainData):
    """
    Represents a website.
    """

    pass
