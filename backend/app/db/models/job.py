"""Job model — transformation job and related issues."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.data_source import DataSource
    from app.db.models.organization import Organization
    from app.db.models.project import Project


class JobStatus(str, enum.Enum):
    """Lifecycle status of a transformation job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueType(str, enum.Enum):
    """Severity of a job issue."""

    WARNING = "warning"
    ERROR = "error"


class TransformationJob(Base):
    """A background job to transform a DataSource into FHIR resources."""

    __tablename__ = "transformation_jobs"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=JobStatus.PENDING,
    )

    # Progress tracking
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Output and errors
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped[Project] = relationship()
    organization: Mapped[Organization] = relationship()
    data_source: Mapped[DataSource] = relationship()
    issues: Mapped[list[JobIssue]] = relationship(
        back_populates="job", cascade="all, delete-orphan", lazy="selectin"
    )


class JobIssue(Base):
    """An issue (error or warning) encountered during transformation."""

    __tablename__ = "job_issues"

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transformation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    row_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issue_type: Mapped[IssueType] = mapped_column(
        Enum(IssueType, name="issue_type", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    field_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    job: Mapped[TransformationJob] = relationship(back_populates="issues")
