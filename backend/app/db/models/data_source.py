"""DataSource model — CSV or API data source within a project.

Tracks the lifecycle of data ingestion: upload → preview → ready.
Stores column metadata and preview data for the mapping step.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.mapping import MappingRule
    from app.db.models.organization import Organization
    from app.db.models.project import Project


class DataSourceType(str, enum.Enum):
    """Type of data source."""

    CSV = "csv"
    API = "api"


class DataSourceStatus(str, enum.Enum):
    """Lifecycle status of a data source.

    Transitions: pending → uploaded → previewed → ready
                 any → error
    """

    PENDING = "pending"
    UPLOADED = "uploaded"
    PREVIEWED = "previewed"
    READY = "ready"
    ERROR = "error"


class DataSource(Base):
    """A data source (CSV file or API endpoint) attached to a project.

    Contains file metadata, column information (after preview),
    and sample rows for the UI preview table.
    """

    __tablename__ = "data_sources"

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[DataSourceType] = mapped_column(
        Enum(DataSourceType, name="data_source_type", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    status: Mapped[DataSourceStatus] = mapped_column(
        Enum(DataSourceStatus, name="data_source_status", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DataSourceStatus.PENDING,
    )

    # ── CSV fields ──
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── API fields (stub for Week 2) ──
    api_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    api_method: Mapped[str | None] = mapped_column(
        String(10), nullable=True, default="GET"
    )
    api_headers: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # ── Column metadata (populated after preview) ──
    columns: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    preview_data: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )

    # ── Error tracking ──
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ──
    project: Mapped[Project] = relationship(back_populates="data_sources")
    organization: Mapped[Organization] = relationship()
    mapping_rules: Mapped[list[MappingRule]] = relationship(
        back_populates="data_source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
