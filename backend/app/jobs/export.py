"""Background task for exporting FHIR NDJSON to a target server."""

import json
import logging
from uuid import UUID

from app.db.models.job import TransformationJob
from app.db.session import async_session_factory
from app.fhir.exporter import FHIRExporter
from app.storage.local import LocalStorage

logger = logging.getLogger(__name__)

async def process_export_job(job_id: UUID, target_url: str, auth_token: str | None, bundle_type: str) -> None:
    """Read the NDJSON output of a job and export it as a FHIR bundle."""
    async with async_session_factory() as session:
        job = await session.get(TransformationJob, job_id)
        if not job or not job.output_file_path:
            logger.error(f"Cannot export job {job_id}: No output file found.")
            return

        storage = LocalStorage()
        target_path = storage._resolve_path(job.output_file_path)

        if not target_path.exists():
            logger.error(f"Cannot export job {job_id}: File missing on disk.")
            return

        resources = []
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        resources.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to read NDJSON for job {job_id}: {str(e)}")
            return

        exporter = FHIRExporter(base_url=target_url, token=auth_token)
        try:
            # In a production environment with huge files, we would chunk these into multiple bundles.
            # For the MVP, we assume the dataset fits into memory and a single request.
            await exporter.export_bundle(resources, bundle_type=bundle_type)
            logger.info(f"Successfully exported {len(resources)} resources for job {job_id} using {bundle_type} bundle.")
        except Exception as e:
            logger.error(f"Failed to export job {job_id}: {str(e)}")
