"""Organization model — tenant boundary for multi-tenancy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.user import User


class Organization(Base):
    """Tenant boundary. Every user and project belongs to exactly one organization.

    All resource queries MUST filter by organization_id to enforce tenant isolation.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    users: Mapped[list[User]] = relationship(back_populates="organization", lazy="selectin")
    projects: Mapped[list[Project]] = relationship(
        back_populates="organization", lazy="selectin"
    )
