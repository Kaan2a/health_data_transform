"""Authentication endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.models.organization import Organization
from app.db.models.user import User


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(
        self, client: AsyncClient, test_user: User
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@hospital.com", "password": "Test1234!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["expires_in"] > 0

    async def test_login_wrong_password(
        self, client: AsyncClient, test_user: User
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@hospital.com", "password": "WrongPass1!"},
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_FAILED"

    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@hospital.com", "password": "Test1234!"},
        )
        assert response.status_code == 401

    async def test_login_invalid_email_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "Test1234!"},
        )
        assert response.status_code == 422

    async def test_login_short_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@hospital.com", "password": "short"},
        )
        assert response.status_code == 422


class TestRegister:
    """Tests for POST /api/v1/auth/register (dev-only)."""

    async def test_register_with_new_org(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@neworg.com",
                "password": "Admin123!",
                "organization_name": "New Hospital",
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == "admin@neworg.com"
        assert data["role"] == "owner"

    async def test_register_with_existing_org(
        self, client: AsyncClient, test_org: Organization
    ) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "staff@hospital.com",
                "password": "Staff123!",
                "organization_id": str(test_org.id),
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["role"] == "admin"
        assert data["organization_id"] == str(test_org.id)

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user: User
    ) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@hospital.com",
                "password": "Test1234!",
                "organization_name": "Another Org",
            },
        )
        assert response.status_code == 409

    async def test_register_missing_org_info(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@hospital.com",
                "password": "New12345!",
            },
        )
        assert response.status_code == 422
