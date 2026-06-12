"""Authentication request/response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    """Registration payload (dev-only endpoint).

    Creates a new user. If organization_name is provided and no
    organization_id is given, a new organization is created.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization_name: str | None = Field(None, max_length=255)
    organization_id: UUID | None = None


class TokenResponse(BaseModel):
    """JWT token response after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """Public user representation (never includes password_hash)."""

    id: UUID
    email: str
    role: str
    organization_id: UUID

    model_config = {"from_attributes": True}
