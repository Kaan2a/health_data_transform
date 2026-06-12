"""Storage factory — returns the configured storage backend.

Reads ``settings.STORAGE_BACKEND`` to determine which implementation to use.
Provides a FastAPI-compatible dependency via ``get_storage()``.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.storage.base import StorageBackend
from app.storage.gcs import GCSStorage
from app.storage.local import LocalStorage


@lru_cache(maxsize=1)
def _create_storage() -> StorageBackend:
    """Create and cache the storage backend instance."""
    backend = settings.STORAGE_BACKEND.lower()

    if backend == "local":
        return LocalStorage()  # type: ignore[return-value]
    elif backend == "gcs":
        return GCSStorage(bucket_name=settings.GCS_BUCKET_NAME)  # type: ignore[return-value]
    else:
        raise ValueError(f"Unknown storage backend: {backend}")


def get_storage() -> StorageBackend:
    """FastAPI dependency that returns the configured storage backend.

    Usage::

        @router.post("/upload")
        async def upload(storage: StorageBackend = Depends(get_storage)):
            await storage.save("key", data)
    """
    return _create_storage()
