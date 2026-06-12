"""Project CRUD endpoints — create and list projects within an organization."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AuthenticatedUser, DbSession
from app.api.v1.schemas.common import DataResponse
from app.api.v1.schemas.project import ProjectCreate, ProjectResponse
from app.core.exceptions import NotFoundError
from app.core.logging import request_id_ctx
from app.db.models.project import Project
from app.db.repository import Repository

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=DataResponse[ProjectResponse], status_code=201)
async def create_project(
    body: ProjectCreate,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict:
    """Create a new conversion project.

    The project is automatically scoped to the authenticated user's organization.
    """
    repo = Repository(db)

    project = Project(
        name=body.name,
        resource_type=body.resource_type,
        fhir_version=body.fhir_version,
        description=body.description,
        organization_id=user.organization_id,
    )
    project = await repo.create(project)

    return {
        "data": ProjectResponse.model_validate(project),
        "requestId": request_id_ctx.get() or "",
    }


@router.get("", response_model=DataResponse[list[ProjectResponse]])
async def list_projects(
    user: AuthenticatedUser,
    db: DbSession,
) -> dict:
    """List all projects for the authenticated user's organization.

    Results are ordered by creation date (newest first) and
    filtered by organization_id for tenant isolation.
    """
    repo = Repository(db)

    projects = await repo.list_all(
        Project,
        org_id=user.organization_id,
    )

    return {
        "data": [ProjectResponse.model_validate(p) for p in projects],
        "requestId": request_id_ctx.get() or "",
    }


@router.get("/{project_id}", response_model=DataResponse[ProjectResponse])
async def get_project(
    project_id: UUID,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict:
    """Get a single project by ID (org-scoped)."""
    repo = Repository(db)

    project = await repo.get_by_id(
        Project,
        project_id,
        org_id=user.organization_id,
    )
    if not project:
        raise NotFoundError("Proje", str(project_id))

    return {
        "data": ProjectResponse.model_validate(project),
        "requestId": request_id_ctx.get() or "",
    }
