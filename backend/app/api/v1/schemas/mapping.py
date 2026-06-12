"""Pydantic schemas for Mapping API."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.project import FhirResourceType


class MappingRuleBase(BaseModel):
    """Base mapping rule schema."""

    source_field: str = Field(..., description="Name of the source column/field")
    target_fhir_field: str = Field(..., description="FHIR JSON path to map to")
    transformation_type: str = Field("direct", description="Type of transformation to apply")
    transformation_config: dict[str, Any] | None = Field(None, description="Configuration for transformation")
    value_map: dict[str, str] | None = Field(None, description="Dictionary mapping source values to FHIR standard values")
    masking_type: str = Field("NONE", description="Masking strategy (NONE, HASH, REDACT, PARTIAL)")


class MappingRuleCreate(MappingRuleBase):
    """Schema for creating a mapping rule."""
    pass


class MappingRuleUpdate(MappingRuleBase):
    """Schema for updating a mapping rule."""
    pass


class MappingRuleResponse(MappingRuleBase):
    """Schema for mapping rule response."""

    id: UUID
    project_id: UUID
    organization_id: UUID
    data_source_id: UUID

    model_config = ConfigDict(from_attributes=True)


class FhirSchemaField(BaseModel):
    """Schema for a FHIR target field definition."""

    path: str
    type: str
    description: str


class AutoMapRequest(BaseModel):
    """Request for auto-mapping suggestions."""

    columns: list[str]


class BatchMappingRequest(BaseModel):
    """Request to save multiple mapping rules at once."""

    rules: list[MappingRuleCreate]
