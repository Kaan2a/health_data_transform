"""Data source request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.db.models.data_source import DataSourceStatus, DataSourceType


class DataSourceCreate(BaseModel):
    """Payload for creating a new data source."""

    name: str = Field(min_length=1, max_length=255)
    type: DataSourceType

    # API-specific fields (optional, only for type=api)
    api_url: str | None = Field(None, max_length=2048)
    api_method: str | None = Field(None, pattern=r"^(GET|POST|PUT)$")
    api_headers: dict[str, str] | None = None


class ColumnInfoResponse(BaseModel):
    """Column metadata from CSV preview."""

    name: str
    inferred_type: str
    sample_values: list[str]
    null_count: int
    total_count: int


class CsvPreviewResponse(BaseModel):
    """CSV preview with column metadata and sample rows."""

    columns: list[ColumnInfoResponse]
    preview_rows: list[dict[str, str]]
    total_rows: int
    encoding: str
    delimiter: str


class UploadResponse(BaseModel):
    """Response after successful file upload."""

    file_name: str
    file_size_bytes: int
    status: DataSourceStatus


class DataSourceResponse(BaseModel):
    """Public data source representation."""

    id: UUID
    project_id: UUID
    organization_id: UUID
    name: str
    type: DataSourceType
    status: DataSourceStatus

    # CSV fields
    file_path: str | None
    file_name: str | None
    file_size_bytes: int | None
    row_count: int | None

    # API fields
    api_url: str | None
    api_method: str | None
    api_headers: dict[str, Any] | None

    # Column metadata
    columns: list[dict[str, Any]] | None
    preview_data: list[dict[str, Any]] | None

    # Error
    error_message: str | None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
