"""API endpoints for analytics and dashboard."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.db.models.project import Project
from app.db.models.job import TransformationJob

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DashboardStats(BaseModel):
    total_projects: int
    total_jobs: int
    total_rows_processed: int
    total_rows_success: int
    total_rows_failed: int

    model_config = ConfigDict(from_attributes=True)


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Get high-level statistics for the current organization's dashboard."""
    org_id = current_user.organization_id

    # 1. Total projects
    stmt_projects = select(func.count(Project.id)).where(Project.organization_id == org_id)
    total_projects = await db.scalar(stmt_projects) or 0

    # 2. Total jobs
    stmt_jobs = select(func.count(TransformationJob.id)).where(TransformationJob.organization_id == org_id)
    total_jobs = await db.scalar(stmt_jobs) or 0

    # 3. Row stats (sum of processed, successful, failed)
    stmt_rows = select(
        func.sum(TransformationJob.processed_rows),
        func.sum(TransformationJob.successful_rows),
        func.sum(TransformationJob.failed_rows),
    ).where(TransformationJob.organization_id == org_id)
    
    row_result = await db.execute(stmt_rows)
    processed, success, failed = row_result.one_or_none() or (0, 0, 0)

    return DashboardStats(
        total_projects=total_projects,
        total_jobs=total_jobs,
        total_rows_processed=processed or 0,
        total_rows_success=success or 0,
        total_rows_failed=failed or 0,
    )
