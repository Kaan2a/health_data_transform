"""Mappings API — endpoints for configuring and previewing FHIR mappings."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AuthenticatedUser, DbSession, get_current_user
from app.api.v1.schemas.mapping import (
    AutoMapRequest,
    BatchMappingRequest,
    FhirSchemaField,
    MappingRuleCreate,
    MappingRuleResponse,
)
from app.db.models.data_source import DataSource
from app.db.models.mapping import MappingRule
from app.db.models.project import Project
from app.db.repository import Repository
from app.services.auto_mapper import AutoMapperService
from app.services.fhir_schema import FHIRSchemaService
from app.services.mapping_preview import MappingPreviewService

router = APIRouter(prefix="/projects/{project_id}", tags=["Mappings"])


@router.get("/fhir-schema", response_model=list[FhirSchemaField])
async def get_fhir_schema(
    project_id: UUID,
    session: DbSession,
    user: AuthenticatedUser,
) -> Any:
    """Get the available FHIR paths for a project's target resource."""
    repo = Repository(session)
    project = await repo.get_by_id(Project, project_id, user.organization_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    schema = FHIRSchemaService.get_schema(project.resource_type)
    return schema


@router.get("/sources/{source_id}/mappings", response_model=list[MappingRuleResponse])
async def list_mapping_rules(
    project_id: UUID,
    source_id: UUID,
    session: DbSession,
    user: AuthenticatedUser,
) -> Any:
    """List all mapping rules for a specific data source."""
    # Validate data source belongs to project and org
    ds_repo = Repository(session)
    source = await ds_repo.get_by_id(DataSource, source_id, user.organization_id)
    if not source or source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found"
        )

    mapping_repo = Repository(session)
    rules = await mapping_repo.list_all(MappingRule, org_id=user.organization_id)
    rules = [r for r in rules if r.data_source_id == source_id]
    return rules


@router.post(
    "/sources/{source_id}/mappings/batch", response_model=list[MappingRuleResponse]
)
async def batch_update_mappings(
    project_id: UUID,
    source_id: UUID,
    request: BatchMappingRequest,
    session: DbSession,
    user: AuthenticatedUser,
) -> Any:
    """Update all mapping rules for a data source (replaces existing)."""
    ds_repo = Repository(session)
    source = await ds_repo.get_by_id(DataSource, source_id, user.organization_id)
    if not source or source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found"
        )

    mapping_repo = Repository(session)
    
    # 1. Delete existing rules for this data source
    existing_rules = await mapping_repo.list_all(MappingRule, org_id=user.organization_id)
    existing_rules = [r for r in existing_rules if r.data_source_id == source_id]
    for rule in existing_rules:
        await mapping_repo.delete(rule)

    # 2. Create new rules
    new_rules = []
    for rule_in in request.rules:
        new_rule = MappingRule(
            project_id=project_id,
            organization_id=user.organization_id,
            data_source_id=source_id,
            source_field=rule_in.source_field,
            target_fhir_field=rule_in.target_fhir_field,
            transformation_type=rule_in.transformation_type,
            transformation_config=rule_in.transformation_config,
        )
        new_rule = await mapping_repo.create(new_rule)
        new_rules.append(new_rule)

    return new_rules


@router.post(
    "/sources/{source_id}/mappings/auto-suggest", response_model=list[MappingRuleCreate]
)
async def auto_suggest_mappings(
    project_id: UUID,
    source_id: UUID,
    request: AutoMapRequest,
    session: DbSession,
    user: AuthenticatedUser,
) -> Any:
    """Generate mapping suggestions based on column names."""
    repo = Repository(session)
    project = await repo.get_by_id(Project, project_id, user.organization_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    suggestions = AutoMapperService.suggest_mappings(
        columns=request.columns, resource_type=project.resource_type
    )
    return suggestions


@router.post("/sources/{source_id}/mappings/preview")
async def preview_mappings(
    project_id: UUID,
    source_id: UUID,
    session: DbSession,
    user: AuthenticatedUser,
) -> Any:
    """Generate a FHIR JSON preview using current mapping rules and preview_data."""
    ds_repo = Repository(session)
    source = await ds_repo.get_by_id(DataSource, source_id, user.organization_id)
    if not source or source.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data source not found"
        )

    if not source.preview_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data source has no preview data. Upload and preview first.",
        )

    mapping_repo = Repository(session)
    rules = await mapping_repo.list_all(MappingRule, org_id=user.organization_id)
    rules = [r for r in rules if r.data_source_id == source_id]

    if not rules:
        return []

    project_repo = Repository(session)
    project = await project_repo.get_by_id(Project, project_id, user.organization_id)

    # In tests project might be mocked or we can just assume it exists
    resource_type = project.resource_type if project else None

    if not resource_type:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
         )

    preview_json = MappingPreviewService.generate_preview(
        preview_data=source.preview_data,
        rules=rules,
        resource_type=resource_type,
    )
    return preview_json
