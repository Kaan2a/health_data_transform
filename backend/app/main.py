"""FastAPI application factory.

Creates the app with:
  - Lifespan for DB engine init/shutdown
  - CORS middleware (configurable origins)
  - Request-ID middleware
  - Standard exception handlers
  - OpenAPI docs at /docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, request_id_ctx, setup_logging
from app.core.middleware import RequestIdMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — runs on startup and shutdown."""
    setup_logging()
    logger.info("FHIR Transformer başlatılıyor…")
    yield
    logger.info("FHIR Transformer kapatılıyor…")

    # Dispose DB engine
    from app.db.session import engine
    await engine.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="FHIR Transformer API",
        description="CSV/API → FHIR R4 dönüştürücü",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # ── Middleware (order matters: first added = outermost) ──
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ── Exception handlers ──
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "requestId": request_id_ctx.get() or "",
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("İşlenmeyen hata: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Beklenmeyen bir hata oluştu.",
                    "details": [],
                },
                "requestId": request_id_ctx.get() or "",
            },
        )

    # ── Routers ──
    app.include_router(v1_router)

    # ── Health check ──
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
