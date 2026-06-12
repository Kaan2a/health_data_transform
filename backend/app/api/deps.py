"""Shared API dependencies — authentication, DB session, org context."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.logging import org_id_ctx, user_id_ctx
from app.core.security import decode_access_token
from app.db.session import get_db

security_scheme = HTTPBearer()


class CurrentUser:
    """Decoded JWT payload representing the authenticated user."""

    def __init__(self, user_id: UUID, organization_id: UUID, role: str) -> None:
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
) -> CurrentUser:
    """Extract and validate the current user from the JWT Bearer token.

    Sets logging context vars for request correlation.
    """
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise AuthenticationError("Geçersiz veya süresi dolmuş token.")

    user_id_str = payload.get("sub")
    org_id_str = payload.get("org")
    role = payload.get("role")

    if not user_id_str or not org_id_str or not role:
        raise AuthenticationError("Token geçersiz bilgi içeriyor.")

    user_id = UUID(user_id_str)
    org_id = UUID(org_id_str)

    # Set logging context
    user_id_ctx.set(str(user_id))
    org_id_ctx.set(str(org_id))

    return CurrentUser(user_id=user_id, organization_id=org_id, role=role)


def require_role(*allowed_roles: str):
    """Dependency factory that checks if user has one of the allowed roles."""

    async def _check(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if user.role not in allowed_roles:
            raise ForbiddenError("Bu işlem için yetkiniz yok.")
        return user

    return _check


# Common dependency type aliases
DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
