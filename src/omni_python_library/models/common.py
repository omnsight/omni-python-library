from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ArangoData(BaseModel):
    """
    Base class for data stored in ArangoDB, containing system fields.
    """

    id: Optional[str] = Field(default=None, alias="_id", description="ArangoDB document ID")
    key: Optional[str] = Field(default=None, alias="_key", description="ArangoDB document key")
    rev: Optional[str] = Field(default=None, alias="_rev", description="ArangoDB document revision")

    created_at: Optional[int] = Field(default=None, ge=0, description="Data creation timestamp")
    updated_at: Optional[int] = Field(default=None, ge=0, description="Data update timestamp")

    model_config = ConfigDict(populate_by_name=True)


class Permissive(BaseModel):
    """
    Base class for permission-related fields.
    """

    owner: str = Field(default=None, max_length=100, description="Owner of the document")
    read: List[str] = Field(default_factory=list, max_length=100, description="Users/Roles with read access")
    write: List[str] = Field(default_factory=list, max_length=100, description="Users/Roles with write access")


class LocationData(BaseModel):
    """
    Represents geographical location data.
    """

    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    country_code: str = Field(..., max_length=2, description="ISO country code")
    administrative_area: str = Field(..., max_length=100, description="Administrative area (e.g., state, province)")
    sub_administrative_area: str = Field(default="", max_length=100, description="Sub-administrative area")
    locality: str = Field(..., max_length=100, description="Locality (e.g., city, town)")
    sub_locality: str = Field(default="", max_length=100, description="Sub-locality")
    address: str = Field(..., max_length=200, description="Full address")
    postal_code: int = Field(..., ge=0, le=9999999999, description="Postal code")
