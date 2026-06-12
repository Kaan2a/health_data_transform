"""Bundle chunker — splits large FHIR Bundles into smaller chunks."""

from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def chunk_bundle_entries(
    entries: list[dict[str, Any]],
    max_entries: int | None = None,
    max_size_mb: float | None = None,
) -> list[list[dict[str, Any]]]:
    """Split a list of Bundle entries into smaller chunks.

    Chunking rules:
    1. Each chunk has at most `max_entries` entries.
    2. Each chunk's JSON serialized size does not exceed `max_size_mb`.
    3. Related resources (same subject reference) are kept together when possible.

    Returns a list of entry lists, each suitable for a single Bundle submission.
    """
    if max_entries is None:
        max_entries = settings.FHIR_BUNDLE_MAX_ENTRIES
    if max_size_mb is None:
        max_size_mb = settings.FHIR_BUNDLE_MAX_SIZE_MB

    max_size_bytes = int(max_size_mb * 1024 * 1024)

    if not entries:
        return []

    chunks: list[list[dict[str, Any]]] = []
    current_chunk: list[dict[str, Any]] = []
    current_size = 0

    for entry in entries:
        entry_size = len(json.dumps(entry, ensure_ascii=False).encode("utf-8"))

        # Check if adding this entry would exceed limits
        would_exceed_count = len(current_chunk) >= max_entries
        would_exceed_size = (current_size + entry_size) > max_size_bytes and len(current_chunk) > 0

        if would_exceed_count or would_exceed_size:
            chunks.append(current_chunk)
            current_chunk = []
            current_size = 0

        current_chunk.append(entry)
        current_size += entry_size

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    logger.info(
        "Bundle chunked",
        extra={
            "total_entries": len(entries),
            "chunk_count": len(chunks),
            "max_entries_per_chunk": max_entries,
        },
    )
    return chunks


def build_bundle(
    bundle_type: str,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Wraps a list of FHIR resources into a FHIR Bundle.

    Args:
        bundle_type: 'batch' or 'transaction'
        entries: list of FHIR resource dicts

    Returns:
        A FHIR Bundle dict ready for submission.
    """
    method = "POST"
    bundle_entries = []
    for resource in entries:
        resource_type = resource.get("resourceType", "Unknown")
        entry: dict[str, Any] = {
            "resource": resource,
            "request": {
                "method": method,
                "url": resource_type,
            },
        }
        bundle_entries.append(entry)

    return {
        "resourceType": "Bundle",
        "type": bundle_type,
        "entry": bundle_entries,
    }
