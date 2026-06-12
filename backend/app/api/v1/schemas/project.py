"""Project request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.models.project import FhirResourceType


class ProjectCreate(BaseModel):
    """Payload for creating a new project."""

    name: str = Field(min_length=1, max_length=255)
    resource_type: FhirResourceType
    description: str | None = Field(None, max_length=1000)
    fhir_version: str = Field(default="4.0.1", pattern=r"^\d+\.\d+\.\d+$")


class ProjectUpdate(BaseModel):
    """Payload for updating a project (partial update)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class ProjectResponse(BaseModel):
    """Public project representation."""

    id: UUID
    name: str
    fhir_version: str
    resource_type: FhirResourceType
    description: str | None
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
