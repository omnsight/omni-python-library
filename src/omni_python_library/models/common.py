from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ArangoData(BaseModel):
    """
    Base class for data stored in ArangoDB, containing system fields.
    """

    id: str = Field(alias="_id", description="ArangoDB document ID")
    key: str = Field(alias="_key", description="ArangoDB document key")
    rev: str = Field(alias="_rev", description="ArangoDB document revision")

    model_config = ConfigDict(populate_by_name=True)


class Permissive(BaseModel):
    """
    Base class for permission-related fields.
    """

    owner: str = Field(description="Owner of the document")
    read: List[str] = Field(default_factory=list, description="Users/Roles with read access")
    write: List[str] = Field(default_factory=list, description="Users/Roles with write access")


class LocationData(BaseModel):
    """
    Represents geographical location data.
    """

    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    country_code: str = Field(..., description="ISO country code")
    administrative_area: str = Field(..., description="Administrative area (e.g., state, province)")
    sub_administrative_area: str = Field(..., description="Sub-administrative area")
    locality: str = Field(..., description="Locality (e.g., city, town)")
    sub_locality: str = Field(..., description="Sub-locality")
    address: str = Field(..., description="Full address")
    postal_code: int = Field(..., description="Postal code")
