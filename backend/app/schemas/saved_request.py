"""Pydantic schemas for SavedRequest entity."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


class SavedRequestBase(BaseModel):
    """Shared saved request attributes."""

    name: str = Field(..., min_length=1, max_length=150, description="Request title")
    method: str = Field("GET", description="HTTP Method (GET, POST, PUT, PATCH, DELETE)")
    url: str = Field(..., min_length=1, max_length=2000, description="Target URL")
    headers: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom headers")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="URL query parameters")
    body: Optional[str] = Field(None, description="Request body payload")
    assertions: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Automated response assertions"
    )

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in VALID_METHODS:
            raise ValueError(f"Method must be one of {sorted(VALID_METHODS)}")
        return v_upper


class SavedRequestCreate(SavedRequestBase):
    """Schema for saving a new request inside a collection."""
    pass


class SavedRequestUpdate(BaseModel):
    """Schema for updating an existing saved request."""

    name: Optional[str] = Field(None, min_length=1, max_length=150)
    method: Optional[str] = None
    url: Optional[str] = Field(None, min_length=1, max_length=2000)
    headers: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[str] = None
    assertions: Optional[List[Dict[str, Any]]] = None

    @field_validator("method")
    @classmethod
    def validate_method_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.strip().upper()
            if v_upper not in VALID_METHODS:
                raise ValueError(f"Method must be one of {sorted(VALID_METHODS)}")
            return v_upper
        return v


class SavedRequestResponse(SavedRequestBase):
    """Schema returned to API callers."""

    id: int
    collection_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedRequestPagination(BaseModel):
    """Paginated list of saved requests."""

    items: List[SavedRequestResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)

