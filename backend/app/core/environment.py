"""Production environment startup checks."""

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)

def check_production_readiness(settings: Settings) -> None:
    """Verifies that production environment is correctly and securely configured."""
    if settings.ENVIRONMENT != "production":
        logger.info(f"Running in {settings.ENVIRONMENT} mode. Skipping production checks.")
        return

    logger.info("Running production environment checks...")

    # 1. Debug mode must be false
    if settings.DEBUG:
        raise AppError("DEBUG mode is enabled in production!")

    # 2. Default secret key must not be used
    if settings.SECRET_KEY == "change-me-in-production":
        raise AppError("Default SECRET_KEY is used in production! Change it immediately.")

    # 3. CORS wildcard is not allowed
    if "*" in settings.CORS_ORIGINS:
        raise AppError("Wildcard '*' in CORS_ORIGINS is not allowed in production.")

    # 4. SSRF protection must be enabled
    if not settings.SSRF_PROTECTION_ENABLED:
        raise AppError("SSRF protection is disabled in production!")

    # 5. Database URL is required and not empty
    if not settings.DATABASE_URL or settings.DATABASE_URL.strip() == "":
        raise AppError("DATABASE_URL is not configured for production!")

    # 6. Storage configuration check
    if settings.STORAGE_BACKEND == "gcs" and not settings.GCS_BUCKET_NAME and not settings.STORAGE_BUCKET:
        raise AppError("GCS storage backend selected but no bucket configured.")

    logger.info("All production checks passed successfully.")
