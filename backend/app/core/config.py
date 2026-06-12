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
    ENVIRONMENT: str = "development" # development, staging, production
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Security ──
    SSRF_PROTECTION_ENABLED: bool = True
    SSRF_ALLOW_PRIVATE_NETWORKS: bool = False
    SSRF_ALLOW_LOOPBACK: bool = False
    SSRF_ALLOW_LINK_LOCAL: bool = False
    SSRF_FOLLOW_REDIRECTS: bool = False
    SSRF_DEV_ALLOWED_DESTINATIONS: list[str] = ["http://mock-api:5000"]
    # Deprecated/Old field kept for compatibility or updated
    SSRF_DEV_ALLOWLIST: list[str] = ["mock-api:5000"]
    
    RATE_LIMIT_DEFAULT: str = "100/minute"

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
    STORAGE_BUCKET: str | None = None
    GCS_BUCKET_NAME: str | None = None

    # ── File Upload ──
    MAX_UPLOAD_SIZE_MB: int = 25

    # ── Worker & Job ──
    WORKER_CONCURRENCY: int = 2
    JOB_TIMEOUT_SECONDS: int = 300

    # ── Limits & Timeouts ──
    API_CONNECT_TIMEOUT_SECONDS: int = 5
    API_READ_TIMEOUT_SECONDS: int = 30
    API_MAX_RESPONSE_SIZE_MB: int = 20

    FHIR_CONNECT_TIMEOUT_SECONDS: int = 10
    FHIR_READ_TIMEOUT_SECONDS: int = 60
    FHIR_MAX_RETRIES: int = 3

    FHIR_BUNDLE_MAX_ENTRIES: int = 100
    FHIR_BUNDLE_MAX_SIZE_MB: int = 10

    # ── FHIR Validator ──
    FHIR_VALIDATOR_URL: str | None = None

    # ── Logging & Monitoring ──
    LOG_FORMAT: str = "text" # 'json' or 'text'
    SENTRY_DSN: str | None = None

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


settings = Settings()
