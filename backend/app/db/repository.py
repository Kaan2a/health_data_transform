"""Generic async CRUD repository with organization-scoped filtering.

Every query enforces org_id filtering to maintain tenant isolation.
"""

from __future__ import annotations

from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class Repository:
    """Generic repository for async CRUD operations.

    All list/get operations filter by organization_id to enforce tenant isolation.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, model: ModelT) -> ModelT:
        """Insert a new record and return it with generated fields."""
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def get_by_id(
        self,
        model_class: type[ModelT],
        record_id: UUID,
        org_id: UUID | None = None,
    ) -> ModelT | None:
        """Fetch a single record by ID, optionally scoped to an organization."""
        stmt = select(model_class).where(model_class.id == record_id)

        if org_id is not None and hasattr(model_class, "organization_id"):
            stmt = stmt.where(model_class.organization_id == org_id)  # type: ignore[attr-defined]

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        model_class: type[ModelT],
        org_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Any | None = None,
    ) -> list[ModelT]:
        """List records, optionally filtered by organization."""
        stmt = select(model_class)

        if org_id is not None and hasattr(model_class, "organization_id"):
            stmt = stmt.where(model_class.organization_id == org_id)  # type: ignore[attr-defined]

        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(model_class.created_at.desc())

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        instance: ModelT,
        update_data: dict[str, Any],
    ) -> ModelT:
        """Update an existing record with partial data."""
        for key, value in update_data.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        """Delete a record."""
        await self.session.delete(instance)
        await self.session.flush()

    async def get_user_by_email(
        self,
        model_class: type[ModelT],
        email: str,
    ) -> ModelT | None:
        """Fetch a user by email (for authentication)."""
        stmt = select(model_class).where(model_class.email == email)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
