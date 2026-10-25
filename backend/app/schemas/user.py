"""Pydantic schemas for User and Authentication."""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserBase(BaseModel):
    """Shared user attributes."""

    email: str = Field(..., description="User email address")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format without requiring external heavy dependencies."""
        v = v.strip().lower()
        if not re.match(EMAIL_REGEX, v):
            raise ValueError("Invalid email format.")
        return v


class UserCreate(UserBase):
    """Registration schema."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters, maximum 128 characters)",
    )


class UserLogin(BaseModel):
    """JSON login schema."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(UserBase):
    """Public user profile schema (never exposes hashed_password)."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT bearer token response."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload data."""

    sub: Optional[str] = None
    exp: Optional[int] = None

