"""V1 API router — aggregates all sub-routers under /api/v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.data_sources import router as data_sources_router
from app.api.v1.mappings import router as mappings_router
from app.api.v1.projects import router as projects_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.analytics import router as analytics_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(projects_router)
v1_router.include_router(data_sources_router)
v1_router.include_router(mappings_router)
v1_router.include_router(jobs_router)
v1_router.include_router(analytics_router)
