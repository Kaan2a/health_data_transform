"""Application exception classes with structured error codes.

All exceptions follow the normalized error response format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message.",
        "details": [...]
    },
    "requestId": "req_..."
}
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error with a machine-readable code and HTTP status."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str | None = None) -> None:
        detail = f"{resource} bulunamadı"
        if identifier:
            detail = f"{resource} ({identifier}) bulunamadı"
        super().__init__(
            message=detail,
            code="NOT_FOUND",
            status_code=404,
        )


class AuthenticationError(AppError):
    """Invalid credentials or expired token."""

    def __init__(self, message: str = "Kimlik doğrulama başarısız.") -> None:
        super().__init__(
            message=message,
            code="AUTH_FAILED",
            status_code=401,
        )


class ForbiddenError(AppError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Bu işlem için yetkiniz yok.") -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
        )


class ValidationError(AppError):
    """Request validation or business rule violation."""

    def __init__(
        self,
        message: str = "Doğrulama hatası.",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class ConflictError(AppError):
    """Duplicate or conflicting state."""

    def __init__(self, message: str = "Kaynak zaten mevcut.") -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
        )
