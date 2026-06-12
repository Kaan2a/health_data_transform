"""Project model — conversion project scoped to an organization."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.data_source import DataSource
    from app.db.models.mapping import MappingRule
    from app.db.models.organization import Organization


class FhirResourceType(str, enum.Enum):
    """Supported FHIR resource types for transformation.

    MVP supports Patient and Observation only.
    """

    PATIENT = "Patient"
    OBSERVATION = "Observation"


class Project(Base):
    """A conversion project targeting a specific FHIR resource type.

    Each project contains data sources, mapping templates, and conversion jobs.
    All projects are scoped to an organization for tenant isolation.
    """

    __tablename__ = "projects"

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fhir_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="4.0.1",
    )
    resource_type: Mapped[FhirResourceType] = mapped_column(
        Enum(FhirResourceType, name="fhir_resource_type", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    organization: Mapped[Organization] = relationship(back_populates="projects")
    data_sources: Mapped[list[DataSource]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    mapping_rules: Mapped[list[MappingRule]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
