"""Standard API response and error schemas.

All API responses follow this envelope:
  Success: {"data": ..., "requestId": "req_..."}
  Error:   {"error": {"code": "...", "message": "...", "details": [...]}, "requestId": "req_..."}
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Individual error detail within a validation error."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorBody(BaseModel):
    """Error body matching the normalized error format from the spec."""

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    error: ErrorBody
    requestId: str = ""


class DataResponse(BaseModel, Generic[T]):
    """Standard success response envelope wrapping any data type."""

    data: T
    requestId: str = ""


class PaginatedData(BaseModel, Generic[T]):
    """Paginated list wrapper with total count."""

    items: list[T]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    """Simple message response for actions like delete."""

    message: str
    requestId: str = ""
