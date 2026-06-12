"""FHIR Server sender — submits Bundles to a target FHIR server with retry."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# HTTP statuses eligible for retry
RETRYABLE_STATUS_CODES = {429, 502, 503, 504}

# Maximum retry count and backoff base
MAX_RETRIES = settings.FHIR_MAX_RETRIES


class FHIRSenderError(Exception):
    """Raised when FHIR submission encounters an unrecoverable error."""

    def __init__(self, message: str, status_code: int | None = None, outcome: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.outcome = outcome


async def check_capability_statement(
    base_url: str,
    auth_header: str | None = None,
) -> dict[str, Any]:
    """Fetch the FHIR server's CapabilityStatement from /metadata.

    Returns the parsed JSON. Raises FHIRSenderError on failure.
    """
    url = f"{base_url.rstrip('/')}/metadata"
    headers: dict[str, str] = {"Accept": "application/fhir+json"}
    if auth_header:
        headers["Authorization"] = auth_header

    timeout = httpx.Timeout(
        connect=settings.FHIR_CONNECT_TIMEOUT_SECONDS,
        read=settings.FHIR_READ_TIMEOUT_SECONDS,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            logger.info("CapabilityStatement fetched", extra={"fhir_server": base_url})
            return data
        except httpx.HTTPStatusError as e:
            raise FHIRSenderError(
                f"FHIR server returned {e.response.status_code} for /metadata",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise FHIRSenderError(f"Failed to connect to FHIR server: {e}")


def supports_bundle_type(capability: dict[str, Any], bundle_type: str) -> bool:
    """Check if the FHIR server supports the given bundle type (batch/transaction)."""
    # Most FHIR servers support both; check rest[0].interaction
    try:
        rest_list = capability.get("rest", [])
        for rest in rest_list:
            interactions = rest.get("interaction", [])
            for interaction in interactions:
                code = interaction.get("code", "")
                if code == bundle_type or code == "transaction":
                    return True
    except (KeyError, TypeError):
        pass
    # Default: assume support (many servers don't declare it explicitly)
    return True


async def send_bundle(
    base_url: str,
    bundle: dict[str, Any],
    auth_header: str | None = None,
    retry_count: int = 0,
) -> dict[str, Any]:
    """Send a FHIR Bundle to the server.

    Implements exponential backoff retry for transient errors (429, 502-504).

    Returns the server's response JSON (typically a Bundle with outcomes).
    Raises FHIRSenderError on non-retryable failures.
    """
    url = base_url.rstrip("/")
    headers: dict[str, str] = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
    }
    if auth_header:
        headers["Authorization"] = auth_header

    timeout = httpx.Timeout(
        connect=settings.FHIR_CONNECT_TIMEOUT_SECONDS,
        read=settings.FHIR_READ_TIMEOUT_SECONDS,
    )

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for attempt in range(retry_count, MAX_RETRIES + 1):
            try:
                resp = await client.post(url, json=bundle, headers=headers)

                if resp.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        "Retryable FHIR error, waiting",
                        extra={
                            "status_code": resp.status_code,
                            "attempt": attempt + 1,
                            "wait_seconds": wait,
                        },
                    )
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code >= 400:
                    body = resp.json() if resp.headers.get("content-type", "").startswith("application") else {}
                    raise FHIRSenderError(
                        f"FHIR server returned {resp.status_code}",
                        status_code=resp.status_code,
                        outcome=body,
                    )

                return resp.json()

            except httpx.TimeoutException as e:
                if attempt < MAX_RETRIES:
                    wait = 2 ** attempt
                    logger.warning("FHIR timeout, retrying", extra={"attempt": attempt + 1, "wait_seconds": wait})
                    await asyncio.sleep(wait)
                    continue
                raise FHIRSenderError(f"FHIR server timeout after {MAX_RETRIES} retries: {e}")

            except httpx.RequestError as e:
                if attempt < MAX_RETRIES:
                    wait = 2 ** attempt
                    logger.warning("FHIR connection error, retrying", extra={"attempt": attempt + 1})
                    await asyncio.sleep(wait)
                    continue
                raise FHIRSenderError(f"FHIR server connection failed: {e}")

    # Should not reach here
    raise FHIRSenderError("Exhausted all retry attempts")


def parse_bundle_response(
    response_bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    """Parse the FHIR Bundle response to extract per-entry results.

    Returns a list of dicts with keys:
        status: HTTP status string (e.g. "201 Created")
        location: Resource location (e.g. "Patient/123/_history/1")
        outcome: OperationOutcome if present
    """
    results = []
    entries = response_bundle.get("entry", [])
    for entry in entries:
        response = entry.get("response", {})
        outcome = entry.get("resource") if entry.get("resource", {}).get("resourceType") == "OperationOutcome" else None
        results.append({
            "status": response.get("status", ""),
            "location": response.get("location"),
            "outcome": outcome,
        })
    return results
