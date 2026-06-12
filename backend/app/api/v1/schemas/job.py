"""Pydantic schemas for transformation jobs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.job import IssueType, JobStatus


class JobCreate(BaseModel):
    pass


class JobIssueResponse(BaseModel):
    id: UUID
    job_id: UUID
    row_index: int | None = None
    issue_type: IssueType
    field_name: str | None = None
    message: str

    model_config = ConfigDict(from_attributes=True)


class JobResponse(BaseModel):
    id: UUID
    project_id: UUID
    organization_id: UUID
    data_source_id: UUID
    status: JobStatus
    total_rows: int
    processed_rows: int
    successful_rows: int
    failed_rows: int
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportRequest(BaseModel):
    target_url: str
    auth_token: str | None = None
    bundle_type: str = "transaction"


class ExportResponse(BaseModel):
    status: str
    message: str
