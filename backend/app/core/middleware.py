"""FastAPI middleware for request-ID injection and request logging."""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, org_id_ctx, request_id_ctx, user_id_ctx

logger = get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject a unique request ID into every request/response cycle.

    - Reads an existing X-Request-ID header if provided by a gateway.
    - Otherwise generates a new UUID4 prefixed with 'req_'.
    - Sets context var for downstream log correlation.
    - Returns the request ID in the response header.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:16]}"

        # Set context vars for logging
        token_req = request_id_ctx.set(req_id)
        token_user = user_id_ctx.set(None)
        token_org = org_id_ctx.set(None)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            logger.info(
                "%s %s → %s (%.1fms)",
                request.method,
                request.url.path,
                response.status_code if "response" in dir() else 500,
                duration_ms,
                extra={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": response.status_code if "response" in dir() else 500,
                    "duration_ms": duration_ms,
                },
            )

            # Reset context vars
            request_id_ctx.reset(token_req)
            user_id_ctx.reset(token_user)
            org_id_ctx.reset(token_org)

        response.headers["X-Request-ID"] = req_id
        return response
