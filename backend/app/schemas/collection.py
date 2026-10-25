"""Pydantic Schemas for Collection entity."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CollectionBase(BaseModel):
    """Shared collection attributes."""
    name: str = Field(..., min_length=1, max_length=100, description="Collection name")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")


class CollectionCreate(CollectionBase):
    """Schema for creating a new collection."""
    pass


class CollectionUpdate(BaseModel):
    """Schema for updating an existing collection. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated name")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")


class CollectionResponse(CollectionBase):
    """Schema for returning collection data to API consumers."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionPagination(BaseModel):
    """Paginated collection list response."""
    items: List[CollectionResponse]
    total: int = Field(..., ge=0, description="Total count of collections matching criteria")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of available pages")

