"""User model — authentication and role-based access."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import Organization


class UserRole(str, enum.Enum):
    """User roles within an organization.

    - owner: full access, can manage org settings
    - admin: can create/edit projects, sources, mappings
    - viewer: read-only access to project results
    """

    OWNER = "owner"
    ADMIN = "admin"
    VIEWER = "viewer"


class User(Base):
    """Application user with scoped access to a single organization."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=UserRole.ADMIN,
    )

    # Relationships
    organization: Mapped[Organization] = relationship(back_populates="users")
