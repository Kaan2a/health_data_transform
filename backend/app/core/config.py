"""Core configuration module — loads settings from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings have safe defaults for local development.
    Production deployments MUST override SECRET_KEY and DATABASE_URL.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──
    APP_NAME: str = "FHIR Transformer"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Database ──
    DATABASE_URL: str = (
        "postgresql+asyncpg://fhir_user:fhir_local_pass@localhost:5432/fhir_transformer"
    )

    # ── Authentication ──
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── CORS ──
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Storage ──
    STORAGE_BACKEND: str = "local"  # "local" or "gcs"
    LOCAL_STORAGE_PATH: str = "./uploads"
    GCS_BUCKET_NAME: str | None = None

    # ── File Upload ──
    MAX_UPLOAD_SIZE_MB: int = 25

    # ── Worker ──
    WORKER_CONCURRENCY: int = 2
    JOB_TIMEOUT_SECONDS: int = 300

    # ── FHIR Validator ──
    FHIR_VALIDATOR_URL: str | None = None

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


settings = Settings()
