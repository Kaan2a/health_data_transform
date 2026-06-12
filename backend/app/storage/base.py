"""Abstract storage backend protocol.

All storage implementations must conform to this protocol so the application
can swap between local filesystem, GCS, S3, etc. without changing business logic.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol defining the file storage interface.

    Implementations handle the actual I/O for saving, loading, and deleting files.
    File paths are logical keys like ``{org_id}/{project_id}/{source_id}/{filename}``.
    """

    async def save(self, file_path: str, data: bytes) -> str:
        """Save file data and return the storage key.

        Args:
            file_path: Logical path/key for the file.
            data: Raw file bytes.

        Returns:
            The storage key (may be the same as file_path or a cloud URI).
        """
        ...

    async def load(self, file_path: str) -> bytes:
        """Load file data by storage key.

        Args:
            file_path: Logical path/key for the file.

        Returns:
            The raw file bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...

    async def delete(self, file_path: str) -> None:
        """Delete a file by storage key.

        Args:
            file_path: Logical path/key for the file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...

    async def exists(self, file_path: str) -> bool:
        """Check if a file exists at the given storage key.

        Args:
            file_path: Logical path/key for the file.

        Returns:
            True if the file exists, False otherwise.
        """
        ...
