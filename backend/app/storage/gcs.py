"""Google Cloud Storage backend — stub for future implementation.

Will use ``gcloud-aio-storage`` for async GCS operations.
"""

from __future__ import annotations


class GCSStorage:
    """GCS storage backend — not yet implemented.

    Placeholder that raises NotImplementedError for all operations.
    Full implementation planned for production deployment sprint.
    """

    def __init__(self, bucket_name: str | None = None) -> None:
        self.bucket_name = bucket_name

    async def save(self, file_path: str, data: bytes) -> str:
        raise NotImplementedError("GCS storage not yet implemented.")

    async def load(self, file_path: str) -> bytes:
        raise NotImplementedError("GCS storage not yet implemented.")

    async def delete(self, file_path: str) -> None:
        raise NotImplementedError("GCS storage not yet implemented.")

    async def exists(self, file_path: str) -> bool:
        raise NotImplementedError("GCS storage not yet implemented.")
