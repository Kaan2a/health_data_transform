"""MappingRule model — rules for mapping data source columns to FHIR fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.data_source import DataSource
    from app.db.models.organization import Organization
    from app.db.models.project import Project


class MappingRule(Base):
    """A rule mapping a source column to a target FHIR field."""

    __tablename__ = "mapping_rules"

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

    source_field: Mapped[str] = mapped_column(String(255), nullable=False)
    target_fhir_field: Mapped[str] = mapped_column(String(255), nullable=False)

    transformation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="direct"
    )
    transformation_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    
    value_map: Mapped[dict[str, str] | None] = mapped_column(
        JSON, nullable=True
    )

    masking_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="NONE"
    )

    # ── Relationships ──
    project: Mapped[Project] = relationship()
    organization: Mapped[Organization] = relationship()
    data_source: Mapped[DataSource] = relationship(back_populates="mapping_rules")
