"""Local filesystem storage backend.

Stores files under a configurable root directory, creating nested directories
as needed. Validates paths to prevent directory traversal attacks.
"""

from __future__ import annotations

import os
from pathlib import Path

import aiofiles
import aiofiles.os

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LocalStorage:
    """Local filesystem storage implementation.

    Files are stored under ``{root}/{file_path}`` where root is configured
    via ``settings.LOCAL_STORAGE_PATH``.
    """

    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or settings.LOCAL_STORAGE_PATH).resolve()

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a logical file path to an absolute filesystem path.

        Prevents directory traversal by ensuring the resolved path
        stays within the storage root.

        Raises:
            ValueError: If the path escapes the root directory.
        """
        # Normalize and join
        resolved = (self.root / file_path).resolve()

        # Guard against traversal
        if not str(resolved).startswith(str(self.root)):
            raise ValueError(f"Path traversal detected: {file_path}")

        return resolved

    async def save(self, file_path: str, data: bytes) -> str:
        """Save file data to the local filesystem.

        Creates parent directories automatically.
        """
        target = self._resolve_path(file_path)

        # Create parent directories
        await aiofiles.os.makedirs(target.parent, exist_ok=True)

        async with aiofiles.open(target, "wb") as f:
            await f.write(data)

        logger.info("File saved: %s (%d bytes)", file_path, len(data))
        return file_path

    async def load(self, file_path: str) -> bytes:
        """Load file data from the local filesystem.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        target = self._resolve_path(file_path)

        if not target.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(target, "rb") as f:
            data = await f.read()

        return data

    async def delete(self, file_path: str) -> None:
        """Delete a file from the local filesystem.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        target = self._resolve_path(file_path)

        if not target.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        await aiofiles.os.remove(target)
        logger.info("File deleted: %s", file_path)

        # Clean up empty parent directories up to root
        parent = target.parent
        while parent != self.root:
            try:
                if not any(parent.iterdir()):
                    await aiofiles.os.rmdir(parent)
                    parent = parent.parent
                else:
                    break
            except OSError:
                break

    async def exists(self, file_path: str) -> bool:
        """Check if a file exists on the local filesystem."""
        target = self._resolve_path(file_path)
        return target.exists()
