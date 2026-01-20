from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from omni_python_library.models.common import ArangoData, LocationData, Permissive


# Relation
class RelationMainData(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the relation")
    confidence: Optional[int] = Field(default=None, description="Confidence score")
    label: Optional[str] = Field(default=None, description="Label")
    created_at: Optional[int] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[int] = Field(default=None, description="Update timestamp")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")

    # Edges specific fields
    from_id: Optional[str] = Field(default=None, alias="_from", description="Source document ID")
    to_id: Optional[str] = Field(default=None, alias="_to", description="Target document ID")

    model_config = ConfigDict(populate_by_name=True)


class Relation(ArangoData, Permissive, RelationMainData):
    """
    Represents a relationship between two entities.
    """

    pass


# Event
class EventMainData(BaseModel):
    type: Optional[str] = Field(default=None, description="Type of event")
    location: Optional[LocationData] = Field(default=None, description="Location of the event")
    title: Optional[str] = Field(default=None, description="Title")
    description: Optional[str] = Field(default=None, description="Description")
    happened_at: Optional[int] = Field(default=None, description="Timestamp when the event happened")
    updated_at: Optional[int] = Field(default=None, description="Update timestamp")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Event(ArangoData, Permissive, EventMainData):
    """
    Represents an event.
    """

    pass


# Source
class SourceMainData(BaseModel):
    type: Optional[str] = Field(default=None, description="Type of source")
    url: Optional[str] = Field(default=None, description="URL")
    name: Optional[str] = Field(default=None, description="Name")
    title: Optional[str] = Field(default=None, description="Title")
    description: Optional[str] = Field(default=None, description="Description")
    reliability: Optional[int] = Field(default=None, description="Reliability score")
    created_at: Optional[int] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[int] = Field(default=None, description="Update timestamp")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Source(ArangoData, Permissive, SourceMainData):
    """
    Represents a source of information.
    """

    pass


# Person
class PersonMainData(BaseModel):
    role: Optional[str] = Field(default=None, description="Role")
    name: Optional[str] = Field(default=None, description="Name")
    nationality: Optional[str] = Field(default=None, description="Nationality")
    birth_date: Optional[int] = Field(default=None, description="Birth date timestamp")
    updated_at: Optional[int] = Field(default=None, description="Update timestamp")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    aliases: Optional[List[str]] = Field(default=None, description="Aliases")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Person(ArangoData, Permissive, PersonMainData):
    """
    Represents a person.
    """

    pass


# Organization
class OrganizationMainData(BaseModel):
    type: Optional[str] = Field(default=None, description="Type of organization")
    name: Optional[str] = Field(default=None, description="Name")
    founded_at: Optional[int] = Field(default=None, description="Founded timestamp")
    discovered_at: Optional[int] = Field(default=None, description="Discovered timestamp")
    last_visited: Optional[int] = Field(default=None, description="Last visited timestamp")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Organization(ArangoData, Permissive, OrganizationMainData):
    """
    Represents an organization.
    """

    pass


# Website
class WebsiteMainData(BaseModel):
    url: Optional[str] = Field(default=None, description="URL")
    title: Optional[str] = Field(default=None, description="Title")
    description: Optional[str] = Field(default=None, description="Description")
    founded_at: Optional[int] = Field(default=None, description="Founded timestamp")
    discovered_at: Optional[int] = Field(default=None, description="Discovered timestamp")
    last_visited: Optional[int] = Field(default=None, description="Last visited timestamp")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    attributes: Optional[Dict[str, Any]] = Field(default=None, description="Additional attributes")


class Website(ArangoData, Permissive, WebsiteMainData):
    """
    Represents a website.
    """

    pass
