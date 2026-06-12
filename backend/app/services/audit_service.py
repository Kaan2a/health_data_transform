"""Audit service — records user actions for compliance and debugging."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.audit_log import AuditLog

logger = get_logger(__name__)

# Fields that should NEVER be logged (PHI/PII)
REDACTED_FIELDS = {
    "patient_name", "name", "family", "given",
    "identifier", "tc_kimlik", "ssn",
    "birth_date", "birthDate",
    "authorization", "api_token", "password",
    "secret_key", "csv_row",
}


async def log_audit(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID | None = None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
    details: str | None = None,
) -> AuditLog:
    """Create an audit log entry.

    Automatically redacts any sensitive field names in metadata.
    """
    safe_metadata = _redact_sensitive(metadata) if metadata else None

    entry = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=safe_metadata,
        details=details,
    )
    db.add(entry)
    await db.flush()

    logger.info(
        "Audit log recorded",
        extra={
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": str(user_id) if user_id else None,
        },
    )
    return entry


def _redact_sensitive(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively redacts sensitive field names from metadata."""
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in REDACTED_FIELDS:
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted[key] = _redact_sensitive(value)
        else:
            redacted[key] = value
    return redacted
