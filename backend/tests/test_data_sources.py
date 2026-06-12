"""Tests for data source endpoints — CRUD, upload, preview, org isolation."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_source import DataSource, DataSourceStatus, DataSourceType
from app.db.models.project import FhirResourceType, Project

FIXTURES = Path(__file__).parent / "fixtures"


@pytest_asyncio.fixture
async def test_project(
    db_session: AsyncSession, test_org: Any
) -> Project:
    """Create a test project for data source tests."""
    project = Project(
        name="Test FHIR Project",
        resource_type=FhirResourceType.PATIENT,
        organization_id=test_org.id,
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


class TestCreateDataSource:
    """Test creating data sources."""

    async def test_create_csv_source(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Patient CSV", "type": "csv"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "Patient CSV"
        assert data["type"] == "csv"
        assert data["status"] == "pending"
        assert data["project_id"] == str(test_project.id)

    async def test_create_api_source(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={
                "name": "REST API Source",
                "type": "api",
                "api_url": "http://mock-api:5000/patients",
                "api_method": "GET",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["type"] == "api"
        assert data["api_url"] == "http://mock-api:5000/patients"

    async def test_create_source_invalid_project(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        fake_id = uuid4()
        response = await client.post(
            f"/api/v1/projects/{fake_id}/sources",
            json={"name": "Test", "type": "csv"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_create_source_unauthenticated(
        self,
        client: AsyncClient,
        test_project: Project,
    ) -> None:
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Test", "type": "csv"},
        )
        assert response.status_code == 401

    async def test_create_source_empty_name(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "", "type": "csv"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestUploadCsv:
    """Test CSV file upload."""

    async def test_upload_valid_csv(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        # Create source
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Upload Test", "type": "csv"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        # Upload file
        csv_content = (FIXTURES / "simple.csv").read_bytes()
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}/upload",
            files={"file": ("patients.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["file_name"] == "patients.csv"
        assert data["file_size_bytes"] > 0
        assert data["status"] == "uploaded"

    async def test_upload_rejects_non_csv(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        # Create source
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Bad File", "type": "csv"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}/upload",
            files={"file": ("data.xlsx", b"fake excel content", "application/vnd.ms-excel")},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_upload_rejects_empty_file(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Empty File", "type": "csv"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}/upload",
            files={"file": ("empty.csv", b"", "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_upload_to_api_source_rejected(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "API Source", "type": "api"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}/upload",
            files={"file": ("data.csv", b"a,b\n1,2\n", "text/csv")},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestPreviewCsv:
    """Test CSV preview generation."""

    async def test_preview_detects_columns(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        # Create + upload
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Preview Test", "type": "csv"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        csv_content = (FIXTURES / "simple.csv").read_bytes()
        await client.post(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}/upload",
            files={"file": ("patients.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )

        # Preview
        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}/preview",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["columns"]) == 8
        assert data["total_rows"] == 10
        assert len(data["preview_rows"]) == 10

        # Check type inference
        col_map = {c["name"]: c for c in data["columns"]}
        assert col_map["birth_date"]["inferred_type"] == "date"
        assert col_map["weight_kg"]["inferred_type"] == "number"
        assert col_map["is_active"]["inferred_type"] == "boolean"

    async def test_preview_without_upload(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "No File", "type": "csv"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}/preview",
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListDataSources:
    """Test listing data sources."""

    async def test_list_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/sources",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_list_returns_sources(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        # Create two sources
        await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Source 1", "type": "csv"},
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Source 2", "type": "api"},
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/v1/projects/{test_project.id}/sources",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2


class TestGetDataSource:
    """Test getting a single data source."""

    async def test_get_existing(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Get Test", "type": "csv"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        response = await client.get(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Get Test"

    async def test_get_nonexistent(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        fake_id = uuid4()
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/sources/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteDataSource:
    """Test deleting data sources."""

    async def test_delete_source(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Delete Me", "type": "csv"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "silindi" in response.json()["message"]

        # Verify it's gone
        get_resp = await client.get(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}",
            headers=auth_headers,
        )
        assert get_resp.status_code == 404

    async def test_delete_with_uploaded_file(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        test_project: Project,
    ) -> None:
        # Create + upload
        create_resp = await client.post(
            f"/api/v1/projects/{test_project.id}/sources",
            json={"name": "Delete With File", "type": "csv"},
            headers=auth_headers,
        )
        source_id = create_resp.json()["data"]["id"]

        csv_content = b"a,b\n1,2\n"
        await client.post(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}/upload",
            files={"file": ("test.csv", csv_content, "text/csv")},
            headers=auth_headers,
        )

        # Delete
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/sources/{source_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
