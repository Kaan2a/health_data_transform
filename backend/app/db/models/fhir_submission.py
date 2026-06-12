"""FHIRSubmission models — FHIR server submission tracking."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import Organization
    from app.db.models.project import Project


class SubmissionStatus(str, enum.Enum):
    """Status of FHIR submission."""

    QUEUED = "queued"
    PROCESSING = "processing"
    VALIDATING = "validating"
    SENDING = "sending"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BundleType(str, enum.Enum):
    """FHIR Bundle type for submission."""

    BATCH = "batch"
    TRANSACTION = "transaction"


class SubmissionEntryStatus(str, enum.Enum):
    """Status of individual submission entry."""

    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


class FHIRSubmission(Base):
    """Tracks a FHIR Bundle submission to a target FHIR server."""

    __tablename__ = "fhir_submissions"

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transformation_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Target FHIR server
    fhir_server_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Bundle metadata
    bundle_type: Mapped[BundleType] = mapped_column(
        Enum(BundleType, name="bundle_type", create_constraint=True,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=BundleType.BATCH,
    )
    bundle_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resource_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status", create_constraint=True,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=SubmissionStatus.QUEUED,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Progress (0-100)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Created by (user_id)
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ──
    organization: Mapped[Organization] = relationship()
    project: Mapped[Project] = relationship()
    entries: Mapped[list[FHIRSubmissionEntry]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FHIRSubmissionEntry(Base):
    """Tracks individual resource result in a FHIR submission."""

    __tablename__ = "fhir_submission_entries"

    submission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fhir_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_identifier: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[SubmissionEntryStatus] = mapped_column(
        Enum(SubmissionEntryStatus, name="submission_entry_status", create_constraint=True,
             values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # FHIR OperationOutcome
    operation_outcome: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ──
    submission: Mapped[FHIRSubmission] = relationship(back_populates="entries")
