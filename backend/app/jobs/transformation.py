"""Background worker for data transformation jobs."""

import csv
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.db.models.data_source import DataSource
from app.db.models.job import JobIssue, JobStatus, TransformationJob, IssueType
from app.db.models.mapping import MappingRule
from app.db.session import async_session_factory
from app.fhir.builder import build_fhir_resource
from app.storage.local import LocalStorage

logger = logging.getLogger(__name__)

async def process_transformation_job(job_id: UUID) -> None:
    """
    Background task to process a transformation job.
    1. Reads the DB to get job, data source, and mapping rules.
    2. Reads the CSV file.
    3. Transforms each row to a FHIR resource.
    4. Writes NDJSON output.
    5. Updates job status and issues in DB.
    """
    storage = LocalStorage()
    
    async with async_session_factory() as session:
        # Fetch Job
        job = await session.get(TransformationJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found.")
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        await session.commit()

        try:
            # Fetch Data Source
            data_source = await session.get(DataSource, job.data_source_id)
            if not data_source or not data_source.file_path:
                raise ValueError("Data source or file path not found.")

            # Fetch Mapping Rules
            stmt = select(MappingRule).where(MappingRule.data_source_id == data_source.id)
            result = await session.execute(stmt)
            rules = list(result.scalars().all())

            if not rules:
                raise ValueError("No mapping rules defined for this data source.")

            # Prepare Output File
            output_file_name = f"output_{job.id}.ndjson"
            output_path = storage._resolve_path(output_file_name)
            
            # Count rows and read data
            file_path = storage._resolve_path(data_source.file_path)
            
            processed = 0
            successful = 0
            failed = 0
            issues = []
            
            # Determine resource type from project
            await session.refresh(job, ["project"])
            resource_type = job.project.resource_type.value
            
            # Synchronous file read/write since we're in a background task thread
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                with open(output_path, "w", encoding="utf-8") as out_f:
                    for row_idx, row in enumerate(reader):
                        processed += 1
                        try:
                            fhir_resource = build_fhir_resource(resource_type, row, rules)
                            
                            # Write to NDJSON
                            out_f.write(json.dumps(fhir_resource) + "\n")
                            successful += 1
                            
                        except ValueError as e:
                            failed += 1
                            issues.append(
                                JobIssue(
                                    job_id=job.id,
                                    row_index=row_idx + 1,
                                    issue_type=IssueType.ERROR,
                                    message=str(e),
                                )
                            )
                        
                        # Periodically update progress in DB
                        if processed % 100 == 0:
                            job.processed_rows = processed
                            job.successful_rows = successful
                            job.failed_rows = failed
                            await session.commit()

            # Final update
            job.total_rows = processed
            job.processed_rows = processed
            job.successful_rows = successful
            job.failed_rows = failed
            job.status = JobStatus.COMPLETED
            job.output_file_path = output_file_name
            job.completed_at = datetime.now(timezone.utc)
            
            if issues:
                session.add_all(issues)
                
            await session.commit()
            logger.info(f"Job {job_id} completed successfully. Processed: {processed}")

        except Exception as e:
            logger.exception(f"Job {job_id} failed with error: {str(e)}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await session.commit()
