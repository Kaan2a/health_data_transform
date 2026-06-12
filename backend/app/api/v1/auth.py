"""Authentication endpoints — login and dev-only registration."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.api.v1.schemas.common import DataResponse
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.logging import request_id_ctx
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.organization import Organization
from app.db.models.user import User
from app.db.repository import Repository
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=DataResponse[TokenResponse])
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate user and return a JWT access token.

    The token payload contains user_id, organization_id, and role
    so downstream endpoints can authorize without extra DB lookups.
    """
    repo = Repository(db)
    user = await repo.get_user_by_email(User, body.email)

    if not user or not verify_password(body.password, user.password_hash):
        raise AuthenticationError("E-posta veya şifre hatalı.")

    token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role.value,
    )

    return {
        "data": TokenResponse(
            access_token=token,
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        ),
        "requestId": request_id_ctx.get() or "",
    }


@router.post("/register", response_model=DataResponse[UserResponse])
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Register a new user (dev-only endpoint).

    If organization_name is provided, a new organization is created.
    Otherwise organization_id must reference an existing organization.
    """
    if not settings.DEBUG:
        raise ValidationError("Kayıt yalnızca geliştirme ortamında aktiftir.")

    repo = Repository(db)

    # Check for existing user
    existing = await repo.get_user_by_email(User, body.email)
    if existing:
        raise ConflictError("Bu e-posta adresi zaten kayıtlı.")

    # Resolve organization
    if body.organization_name:
        org = Organization(name=body.organization_name)
        org = await repo.create(org)
        org_id = org.id
    elif body.organization_id:
        org = await repo.get_by_id(Organization, body.organization_id)
        if not org:
            raise ValidationError("Belirtilen organizasyon bulunamadı.")
        org_id = org.id
    else:
        raise ValidationError("organization_name veya organization_id gerekli.")

    # Create user
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        organization_id=org_id,
        role="owner" if body.organization_name else "admin",
    )
    user = await repo.create(user)

    return {
        "data": UserResponse.model_validate(user),
        "requestId": request_id_ctx.get() or "",
    }
