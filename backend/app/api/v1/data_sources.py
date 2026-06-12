"""Data source CRUD + upload + preview endpoints.

Handles CSV file uploads, column detection, and preview generation
within the context of a project.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile

from app.api.deps import AuthenticatedUser, DbSession
from app.api.v1.schemas.common import DataResponse, MessageResponse
from app.api.v1.schemas.data_source import (
    CsvPreviewResponse,
    DataSourceCreate,
    DataSourceResponse,
    UploadResponse,
)
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger, request_id_ctx
from app.db.models.data_source import DataSource, DataSourceStatus, DataSourceType
from app.db.models.project import Project
from app.db.repository import Repository
from app.ingestion.csv_parser import parse_csv_preview
from app.storage.base import StorageBackend
from app.storage.factory import get_storage

logger = get_logger(__name__)

router = APIRouter(prefix="/projects/{project_id}/sources", tags=["Data Sources"])

ALLOWED_EXTENSIONS = {".csv", ".tsv"}


async def _get_project_or_404(
    project_id: UUID, org_id: UUID, repo: Repository
) -> Project:
    """Fetch a project by ID scoped to the org, or raise 404."""
    project = await repo.get_by_id(Project, project_id, org_id=org_id)
    if not project:
        raise NotFoundError("Proje", str(project_id))
    return project


async def _get_source_or_404(
    source_id: UUID, project_id: UUID, org_id: UUID, repo: Repository
) -> DataSource:
    """Fetch a data source by ID scoped to the project and org, or raise 404."""
    source = await repo.get_by_id(DataSource, source_id, org_id=org_id)
    if not source or source.project_id != project_id:
        raise NotFoundError("Veri kaynağı", str(source_id))
    return source


@router.post("", response_model=DataResponse[DataSourceResponse], status_code=201)
async def create_data_source(
    project_id: UUID,
    body: DataSourceCreate,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict:
    """Create a new data source within a project.

    For CSV sources, status starts as 'pending' — upload the file next.
    For API sources, only the metadata is stored (fetching is deferred).
    """
    repo = Repository(db)
    await _get_project_or_404(project_id, user.organization_id, repo)

    if body.type == DataSourceType.API and body.api_url:
        from app.security.ssrf import validate_url_for_ssrf, SSRFError
        try:
            validate_url_for_ssrf(body.api_url)
        except SSRFError as e:
            raise ValidationError(str(e))

    source = DataSource(
        project_id=project_id,
        organization_id=user.organization_id,
        name=body.name,
        type=body.type,
        status=DataSourceStatus.PENDING,
        api_url=body.api_url,
        api_method=body.api_method,
        api_headers=body.api_headers,
    )
    source = await repo.create(source)

    return {
        "data": DataSourceResponse.model_validate(source),
        "requestId": request_id_ctx.get() or "",
    }


@router.post(
    "/{source_id}/upload",
    response_model=DataResponse[UploadResponse],
)
async def upload_csv(
    project_id: UUID,
    source_id: UUID,
    file: UploadFile,
    user: AuthenticatedUser,
    db: DbSession,
    storage: StorageBackend = Depends(get_storage),
) -> dict:
    """Upload a CSV file to an existing data source.

    Validates file extension, size, and source type before saving.
    Updates the source status to 'uploaded'.
    """
    repo = Repository(db)
    source = await _get_source_or_404(
        source_id, project_id, user.organization_id, repo
    )

    # Validate source type
    if source.type != DataSourceType.CSV:
        raise ValidationError("Sadece CSV kaynağına dosya yüklenebilir.")

    # Validate file extension
    filename = file.filename or "upload.csv"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Geçersiz dosya uzantısı: {ext}. İzin verilen: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > settings.max_upload_size_bytes:
        raise ValidationError(
            f"Dosya boyutu çok büyük. Maksimum: {settings.MAX_UPLOAD_SIZE_MB} MB"
        )

    if not content:
        raise ValidationError("Dosya boş.")

    # Build storage key
    storage_key = (
        f"{user.organization_id}/{project_id}/{source_id}/{filename}"
    )

    # Save to storage
    await storage.save(storage_key, content)

    # Update source metadata
    await repo.update(
        source,
        {
            "file_path": storage_key,
            "file_name": filename,
            "file_size_bytes": len(content),
            "status": DataSourceStatus.UPLOADED,
            "error_message": None,
        },
    )

    logger.info(
        "CSV uploaded: source=%s, file=%s, size=%d",
        source_id, filename, len(content),
    )

    return {
        "data": UploadResponse(
            file_name=filename,
            file_size_bytes=len(content),
            status=DataSourceStatus.UPLOADED,
        ),
        "requestId": request_id_ctx.get() or "",
    }


@router.post(
    "/{source_id}/preview",
    response_model=DataResponse[CsvPreviewResponse],
)
async def preview_csv(
    project_id: UUID,
    source_id: UUID,
    user: AuthenticatedUser,
    db: DbSession,
    storage: StorageBackend = Depends(get_storage),
) -> dict:
    """Trigger column detection and preview generation for a CSV source.

    Reads the uploaded file, detects encoding/delimiter, infers column types,
    and stores the metadata and preview rows on the data source.
    """
    repo = Repository(db)
    source = await _get_source_or_404(
        source_id, project_id, user.organization_id, repo
    )

    if source.type != DataSourceType.CSV:
        raise ValidationError("Ön izleme sadece CSV kaynakları için kullanılabilir.")

    if not source.file_path:
        raise ValidationError("Önce bir dosya yükleyin.")

    try:
        # Load file from storage
        file_bytes = await storage.load(source.file_path)

        # Parse CSV
        result = parse_csv_preview(file_bytes)

        # Update source with column metadata and preview
        await repo.update(
            source,
            {
                "columns": [c.to_dict() for c in result.columns],
                "preview_data": result.preview_rows,
                "row_count": result.total_rows,
                "status": DataSourceStatus.PREVIEWED,
                "error_message": None,
            },
        )

        logger.info(
            "CSV preview generated: source=%s, columns=%d, rows=%d",
            source_id, len(result.columns), result.total_rows,
        )

        return {
            "data": CsvPreviewResponse(
                columns=[
                    {
                        "name": c.name,
                        "inferred_type": c.inferred_type,
                        "sample_values": c.sample_values[:5],
                        "null_count": c.null_count,
                        "total_count": c.total_count,
                    }
                    for c in result.columns
                ],
                preview_rows=result.preview_rows,
                total_rows=result.total_rows,
                encoding=result.encoding,
                delimiter=result.delimiter,
            ),
            "requestId": request_id_ctx.get() or "",
        }

    except (ValueError, FileNotFoundError) as e:
        await repo.update(
            source,
            {
                "status": DataSourceStatus.ERROR,
                "error_message": str(e),
            },
        )
        raise ValidationError(str(e))


@router.get("", response_model=DataResponse[list[DataSourceResponse]])
async def list_data_sources(
    project_id: UUID,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict:
    """List all data sources for a project."""
    repo = Repository(db)
    await _get_project_or_404(project_id, user.organization_id, repo)

    from sqlalchemy import select

    stmt = (
        select(DataSource)
        .where(DataSource.project_id == project_id)
        .where(DataSource.organization_id == user.organization_id)
        .order_by(DataSource.created_at.desc())
    )
    result = await db.execute(stmt)
    sources = list(result.scalars().all())

    return {
        "data": [DataSourceResponse.model_validate(s) for s in sources],
        "requestId": request_id_ctx.get() or "",
    }


@router.get("/{source_id}", response_model=DataResponse[DataSourceResponse])
async def get_data_source(
    project_id: UUID,
    source_id: UUID,
    user: AuthenticatedUser,
    db: DbSession,
) -> dict:
    """Get a single data source by ID with full details."""
    repo = Repository(db)
    source = await _get_source_or_404(
        source_id, project_id, user.organization_id, repo
    )

    return {
        "data": DataSourceResponse.model_validate(source),
        "requestId": request_id_ctx.get() or "",
    }


@router.delete(
    "/{source_id}",
    response_model=MessageResponse,
)
async def delete_data_source(
    project_id: UUID,
    source_id: UUID,
    user: AuthenticatedUser,
    db: DbSession,
    storage: StorageBackend = Depends(get_storage),
) -> dict:
    """Delete a data source and its associated file from storage."""
    repo = Repository(db)
    source = await _get_source_or_404(
        source_id, project_id, user.organization_id, repo
    )

    # Delete file from storage if exists
    if source.file_path:
        try:
            await storage.delete(source.file_path)
        except FileNotFoundError:
            logger.warning("File already missing from storage: %s", source.file_path)

    await repo.delete(source)

    logger.info("Data source deleted: %s", source_id)

    return {
        "message": "Veri kaynağı silindi.",
        "requestId": request_id_ctx.get() or "",
    }
