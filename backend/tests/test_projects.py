"""Project endpoint tests — CRUD and tenant isolation."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.organization import Organization
from app.db.models.user import User


class TestCreateProject:
    """Tests for POST /api/v1/projects."""

    async def test_create_patient_project(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={
                "name": "Hasta Dönüşümü",
                "resource_type": "Patient",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "Hasta Dönüşümü"
        assert data["resource_type"] == "Patient"
        assert data["fhir_version"] == "4.0.1"

    async def test_create_observation_project(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={
                "name": "Lab Sonuçları",
                "resource_type": "Observation",
                "description": "Laboratuvar test sonuçları dönüşümü",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["resource_type"] == "Observation"
        assert data["description"] == "Laboratuvar test sonuçları dönüşümü"

    async def test_create_project_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "Test", "resource_type": "Patient"},
        )
        assert response.status_code == 401  # No bearer token

    async def test_create_project_invalid_resource_type(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "Test", "resource_type": "Encounter"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_project_empty_name(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.post(
            "/api/v1/projects",
            json={"name": "", "resource_type": "Patient"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListProjects:
    """Tests for GET /api/v1/projects."""

    async def test_list_empty(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_list_returns_own_projects(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        # Create two projects
        await client.post(
            "/api/v1/projects",
            json={"name": "Proje 1", "resource_type": "Patient"},
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/projects",
            json={"name": "Proje 2", "resource_type": "Observation"},
            headers=auth_headers,
        )

        response = await client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2

    async def test_tenant_isolation(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Projects from another org should NOT be visible."""
        # Create project as test user
        await client.post(
            "/api/v1/projects",
            json={"name": "My Project", "resource_type": "Patient"},
            headers=auth_headers,
        )

        # Create token for a different org
        other_token = create_access_token(
            user_id=uuid4(),
            organization_id=uuid4(),
            role="admin",
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}

        response = await client.get("/api/v1/projects", headers=other_headers)
        assert response.status_code == 200
        assert response.json()["data"] == []  # No access to other org's projects


class TestGetProject:
    """Tests for GET /api/v1/projects/{project_id}."""

    async def test_get_existing_project(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        create_resp = await client.post(
            "/api/v1/projects",
            json={"name": "Test Proje", "resource_type": "Patient"},
            headers=auth_headers,
        )
        project_id = create_resp.json()["data"]["id"]

        response = await client.get(
            f"/api/v1/projects/{project_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Test Proje"

    async def test_get_nonexistent_project(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.get(
            f"/api/v1/projects/{uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404
