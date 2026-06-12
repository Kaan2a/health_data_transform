"""Submission tasks — background FHIR Bundle submission worker."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.fhir_submission import (
    BundleType,
    FHIRSubmission,
    FHIRSubmissionEntry,
    SubmissionEntryStatus,
    SubmissionStatus,
)
from app.services.bundle_chunker import build_bundle, chunk_bundle_entries
from app.services.fhir_sender import (
    FHIRSenderError,
    check_capability_statement,
    parse_bundle_response,
    send_bundle,
)

logger = get_logger(__name__)


async def run_submission(
    db: AsyncSession,
    *,
    submission_id: UUID,
    fhir_resources: list[dict[str, Any]],
    fhir_server_url: str,
    bundle_type: str = "batch",
    auth_header: str | None = None,
) -> FHIRSubmission:
    """Run the full FHIR submission pipeline.

    Steps:
    1. Check CapabilityStatement
    2. Chunk resources into Bundles
    3. Send each Bundle with retry
    4. Parse responses and record entries
    5. Update submission status
    """
    from sqlalchemy import select

    # Fetch submission record
    result = await db.execute(
        select(FHIRSubmission).where(FHIRSubmission.id == submission_id)
    )
    submission = result.scalar_one()
    submission.status = SubmissionStatus.PROCESSING
    submission.started_at = datetime.now(timezone.utc)
    await db.flush()

    try:
        # 1. Check capability
        submission.status = SubmissionStatus.VALIDATING
        await db.flush()

        try:
            capability = await check_capability_statement(fhir_server_url, auth_header)
            logger.info("FHIR server capability verified", extra={"server": fhir_server_url})
        except FHIRSenderError as e:
            logger.warning("Could not fetch CapabilityStatement, proceeding anyway", extra={"error": str(e)})

        # 2. Chunk resources
        chunks = chunk_bundle_entries(fhir_resources)
        submission.bundle_count = len(chunks)
        submission.resource_count = len(fhir_resources)
        submission.status = SubmissionStatus.SENDING
        await db.flush()

        total_success = 0
        total_failure = 0

        # 3. Send each chunk
        for chunk_idx, chunk in enumerate(chunks):
            bundle = build_bundle(bundle_type, chunk)

            try:
                response_data = await send_bundle(
                    fhir_server_url, bundle, auth_header
                )
                # 4. Parse response
                entry_results = parse_bundle_response(response_data)

                for i, entry_result in enumerate(entry_results):
                    status_str = entry_result.get("status", "")
                    http_code = _parse_http_status(status_str)
                    is_success = 200 <= http_code < 300 if http_code else False

                    entry_status = (
                        SubmissionEntryStatus.SUCCESS if is_success
                        else SubmissionEntryStatus.FAILURE
                    )

                    resource = chunk[i] if i < len(chunk) else {}
                    db_entry = FHIRSubmissionEntry(
                        submission_id=submission_id,
                        source_row_number=chunk_idx * len(chunk) + i,
                        resource_type=resource.get("resourceType", "Unknown"),
                        resource_identifier=_extract_identifier(resource),
                        status=entry_status,
                        http_status=http_code,
                        location=entry_result.get("location"),
                        operation_outcome=entry_result.get("outcome"),
                        error_message=_extract_error_message(entry_result.get("outcome")),
                    )
                    db.add(db_entry)

                    if is_success:
                        total_success += 1
                    else:
                        total_failure += 1

            except FHIRSenderError as e:
                # Entire chunk failed
                for i, resource in enumerate(chunk):
                    db_entry = FHIRSubmissionEntry(
                        submission_id=submission_id,
                        source_row_number=chunk_idx * len(chunk) + i,
                        resource_type=resource.get("resourceType", "Unknown"),
                        resource_identifier=_extract_identifier(resource),
                        status=SubmissionEntryStatus.FAILURE,
                        http_status=e.status_code,
                        operation_outcome=e.outcome,
                        error_message=str(e),
                    )
                    db.add(db_entry)
                    total_failure += 1

            # Update progress
            processed = sum(len(c) for c in chunks[: chunk_idx + 1])
            submission.progress = int((processed / len(fhir_resources)) * 100)
            await db.flush()

        # 5. Finalize
        submission.success_count = total_success
        submission.failure_count = total_failure
        submission.completed_at = datetime.now(timezone.utc)
        submission.progress = 100

        if total_failure == 0:
            submission.status = SubmissionStatus.COMPLETED
        elif total_success > 0:
            submission.status = SubmissionStatus.COMPLETED_WITH_ERRORS
        else:
            submission.status = SubmissionStatus.FAILED

        await db.flush()
        await db.commit()

        logger.info(
            "FHIR submission completed",
            extra={
                "submission_id": str(submission_id),
                "success": total_success,
                "failure": total_failure,
            },
        )
        return submission

    except Exception as e:
        submission.status = SubmissionStatus.FAILED
        submission.error_message = str(e)
        submission.completed_at = datetime.now(timezone.utc)
        await db.flush()
        await db.commit()
        logger.exception("FHIR submission failed", extra={"submission_id": str(submission_id)})
        raise


def _parse_http_status(status_str: str) -> int | None:
    """Parse HTTP status from FHIR response status string (e.g. '201 Created')."""
    if not status_str:
        return None
    try:
        return int(status_str.split()[0])
    except (ValueError, IndexError):
        return None


def _extract_identifier(resource: dict[str, Any]) -> str | None:
    """Extract a human-readable identifier from a FHIR resource."""
    identifiers = resource.get("identifier", [])
    if identifiers and isinstance(identifiers, list):
        return identifiers[0].get("value")
    return resource.get("id")


def _extract_error_message(outcome: dict[str, Any] | None) -> str | None:
    """Extract error text from an OperationOutcome resource."""
    if not outcome:
        return None
    issues = outcome.get("issue", [])
    messages = []
    for issue in issues:
        text = issue.get("diagnostics") or issue.get("details", {}).get("text", "")
        if text:
            messages.append(text)
    return "; ".join(messages) if messages else None
