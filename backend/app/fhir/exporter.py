"""FHIR Exporter module for sending resources to an external FHIR server."""

from typing import Any
import httpx
from fastapi import HTTPException

class FHIRExporter:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/fhir+json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
            
    async def export_bundle(self, resources: list[dict[str, Any]], bundle_type: str = "transaction") -> dict[str, Any]:
        """Export a list of resources as a FHIR Bundle (batch or transaction)."""
        if not resources:
            return {"status": "empty", "message": "No resources to export"}

        bundle = {
            "resourceType": "Bundle",
            "type": bundle_type,
            "entry": []
        }

        for resource in resources:
            # Assigning a temporary UUID might be necessary for transaction internal references, 
            # but for a simple POST, we just specify the resource type in url
            resource_type = resource.get("resourceType", "")
            entry = {
                "resource": resource,
                "request": {
                    "method": "POST",
                    "url": resource_type
                }
            }
            bundle["entry"].append(entry)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.base_url,
                    json=bundle,
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                try:
                    # Try to parse FHIR OperationOutcome
                    parsed = e.response.json()
                    if parsed.get("resourceType") == "OperationOutcome":
                        error_detail = parsed.get("issue", [{}])[0].get("diagnostics", error_detail)
                except Exception:
                    pass
                    
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Hedef FHIR sunucusu hatası: {error_detail}"
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"FHIR Sunucusuna bağlanılamadı: {str(e)}")
