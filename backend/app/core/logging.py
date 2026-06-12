"""Structured JSON logging configuration.

Every log line is a JSON object containing:
  - timestamp, level, message
  - request_id, user_id, org_id  (when available from context)
  - endpoint, duration           (when available)

Sensitive fields (authorization headers, passwords, tokens) are NEVER logged.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

# Context variables for request-scoped correlation
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)
org_id_ctx: ContextVar[str | None] = ContextVar("org_id", default=None)


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Inject request-scoped context
        req_id = request_id_ctx.get()
        if req_id:
            log_entry["request_id"] = req_id

        uid = user_id_ctx.get()
        if uid:
            log_entry["user_id"] = uid

        oid = org_id_ctx.get()
        if oid:
            log_entry["org_id"] = oid

        # Include exception info if present
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        # Include any extra fields attached to the record
        for key in ("endpoint", "duration_ms", "status_code", "method"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging() -> None:
    """Configure root logger with JSON formatter to stdout."""
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())

    # Remove existing handlers to avoid duplicates
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    # Suppress noisy third-party loggers
    for name in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger that inherits the JSON formatter."""
    return logging.getLogger(name)
