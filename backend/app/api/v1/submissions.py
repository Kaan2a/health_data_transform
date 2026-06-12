"""API endpoints for FHIR submissions."""

from __future__ import annotations

import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.core.logging import get_logger, request_id_ctx
from app.db.models.fhir_submission import (
    BundleType,
    FHIRSubmission,
    FHIRSubmissionEntry,
    SubmissionStatus,
)
from app.db.models.job import JobStatus, TransformationJob
from app.db.session import get_db
from app.storage.local import LocalStorage

logger = get_logger(__name__)

router = APIRouter(tags=["Submissions"])


# ── Schemas ──


class SubmissionCreateRequest(BaseModel):
    """Request to start a FHIR submission."""

    job_id: UUID = Field(..., description="Transformation job ID to submit")
    fhir_server_url: str = Field(..., description="Target FHIR server base URL")
    bundle_type: str = Field("batch", description="Bundle type: batch or transaction")
    auth_header: str | None = Field(None, description="Authorization header value")


class SubmissionResponse(BaseModel):
    """Response for a FHIR submission."""

    id: UUID
    organization_id: UUID
    project_id: UUID
    job_id: UUID | None
    fhir_server_url: str
    bundle_type: str
    bundle_count: int
    resource_count: int
    success_count: int
    failure_count: int
    status: str
    progress: int
    error_message: str | None
    started_at: Any | None
    completed_at: Any | None
    created_at: Any

    model_config = ConfigDict(from_attributes=True)


class SubmissionEntryResponse(BaseModel):
    """Response for a single submission entry."""

    id: UUID
    submission_id: UUID
    source_row_number: int | None
    resource_type: str
    resource_identifier: str | None
    status: str
    http_status: int | None
    location: str | None
    operation_outcome: dict[str, Any] | None
    error_code: str | None
    error_message: str | None
    created_at: Any

    model_config = ConfigDict(from_attributes=True)


# ── Endpoints ──


@router.post(
    "/projects/{project_id}/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_submission(
    project_id: UUID,
    body: SubmissionCreateRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Start a new FHIR submission from a completed transformation job."""
    # Verify job exists and is completed
    job = await db.get(TransformationJob, body.job_id)
    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED or not job.output_file_path:
        raise HTTPException(
            status_code=400,
            detail="Job is not completed or has no output file.",
        )

    # Resolve bundle type
    try:
        b_type = BundleType(body.bundle_type)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid bundle_type. Use 'batch' or 'transaction'.")

    # Create submission record
    submission = FHIRSubmission(
        organization_id=current_user.organization_id,
        project_id=project_id,
        job_id=body.job_id,
        fhir_server_url=body.fhir_server_url,
        bundle_type=b_type,
        status=SubmissionStatus.QUEUED,
        created_by=current_user.user_id,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # Load FHIR resources from NDJSON output file
    background_tasks.add_task(
        _run_submission_background,
        submission_id=submission.id,
        output_file_path=job.output_file_path,
        fhir_server_url=body.fhir_server_url,
        bundle_type=body.bundle_type,
        auth_header=body.auth_header,
    )

    return submission


async def _run_submission_background(
    submission_id: UUID,
    output_file_path: str,
    fhir_server_url: str,
    bundle_type: str,
    auth_header: str | None,
) -> None:
    """Background task to load NDJSON and run submission."""
    from app.db.session import AsyncSessionFactory

    # Load FHIR resources from NDJSON
    storage = LocalStorage()
    resolved = storage._resolve_path(output_file_path)

    fhir_resources: list[dict[str, Any]] = []
    try:
        with open(resolved, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    fhir_resources.append(json.loads(line))
    except Exception as e:
        logger.error(f"Failed to read NDJSON file: {e}")
        return

    async with AsyncSessionFactory() as db:
        from app.workers.submission_tasks import run_submission
        try:
            await run_submission(
                db,
                submission_id=submission_id,
                fhir_resources=fhir_resources,
                fhir_server_url=fhir_server_url,
                bundle_type=bundle_type,
                auth_header=auth_header,
            )
        except Exception as e:
            logger.exception(f"Submission task failed: {e}")


@router.get(
    "/projects/{project_id}/submissions",
    response_model=list[SubmissionResponse],
)
async def list_submissions(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """List all submissions for a project."""
    stmt = (
        select(FHIRSubmission)
        .where(
            FHIRSubmission.project_id == project_id,
            FHIRSubmission.organization_id == current_user.organization_id,
        )
        .order_by(FHIRSubmission.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionResponse,
)
async def get_submission(
    submission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Get details of a specific submission."""
    submission = await db.get(FHIRSubmission, submission_id)
    if not submission or submission.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@router.get(
    "/submissions/{submission_id}/entries",
    response_model=list[SubmissionEntryResponse],
)
async def get_submission_entries(
    submission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Get all entries (per-resource results) for a submission."""
    submission = await db.get(FHIRSubmission, submission_id)
    if not submission or submission.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Submission not found")

    stmt = (
        select(FHIRSubmissionEntry)
        .where(FHIRSubmissionEntry.submission_id == submission_id)
        .order_by(FHIRSubmissionEntry.source_row_number)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/submissions/{submission_id}/error-report")
async def get_error_report(
    submission_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Download a JSON error report for failed entries."""
    submission = await db.get(FHIRSubmission, submission_id)
    if not submission or submission.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Submission not found")

    stmt = (
        select(FHIRSubmissionEntry)
        .where(
            FHIRSubmissionEntry.submission_id == submission_id,
            FHIRSubmissionEntry.status == "failure",
        )
        .order_by(FHIRSubmissionEntry.source_row_number)
    )
    result = await db.execute(stmt)
    failed_entries = result.scalars().all()

    report = {
        "submission_id": str(submission_id),
        "total_failures": len(failed_entries),
        "errors": [
            {
                "row": e.source_row_number,
                "resource_type": e.resource_type,
                "http_status": e.http_status,
                "error": e.error_message,
                "outcome": e.operation_outcome,
            }
            for e in failed_entries
        ],
    }
    return report


@router.post("/submissions/{submission_id}/retry")
async def retry_submission(
    submission_id: UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Retry a failed or partially failed submission."""
    submission = await db.get(FHIRSubmission, submission_id)
    if not submission or submission.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.status not in (
        SubmissionStatus.FAILED,
        SubmissionStatus.COMPLETED_WITH_ERRORS,
    ):
        raise HTTPException(
            status_code=400,
            detail="Only failed or partially failed submissions can be retried.",
        )

    # Reset submission state
    submission.status = SubmissionStatus.QUEUED
    submission.progress = 0
    submission.success_count = 0
    submission.failure_count = 0
    submission.error_message = None
    submission.started_at = None
    submission.completed_at = None
    await db.commit()

    # Re-queue via the job's output file
    if submission.job_id:
        job = await db.get(TransformationJob, submission.job_id)
        if job and job.output_file_path:
            background_tasks.add_task(
                _run_submission_background,
                submission_id=submission.id,
                output_file_path=job.output_file_path,
                fhir_server_url=submission.fhir_server_url,
                bundle_type=submission.bundle_type.value,
                auth_header=None,
            )

    return {"status": "accepted", "message": "Submission retry has been queued."}
