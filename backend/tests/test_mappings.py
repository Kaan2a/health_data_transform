import pytest
from httpx import AsyncClient

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_source import DataSource, DataSourceType, DataSourceStatus
from app.db.models.project import FhirResourceType, Project

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_org) -> Project:
    project = Project(
        name="Mapping Project",
        resource_type=FhirResourceType.PATIENT,
        organization_id=test_org.id,
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_data_source(db_session: AsyncSession, test_project: Project, test_org) -> DataSource:
    ds = DataSource(
        name="Test CSV",
        type=DataSourceType.CSV,
        status=DataSourceStatus.READY,
        project_id=test_project.id,
        organization_id=test_org.id,
        columns=[
            {"name": "hasta_adi", "inferred_type": "string"},
            {"name": "hasta_soyadi", "inferred_type": "string"},
        ],
        preview_data=[
            {"hasta_adi": "Ahmet", "hasta_soyadi": "Yılmaz"},
            {"hasta_adi": "Ayşe", "hasta_soyadi": "Kaya"},
        ]
    )
    db_session.add(ds)
    await db_session.flush()
    await db_session.refresh(ds)
    return ds


@pytest_asyncio.fixture
async def test_data_source_with_preview(test_data_source: DataSource) -> DataSource:
    return test_data_source


async def test_get_fhir_schema(client: AsyncClient, test_project, auth_headers):
    res = await client.get(
        f"/api/v1/projects/{test_project.id}/fhir-schema", headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Patient schema should have 'name[0].family'
    assert any(field["path"] == "name[0].family" for field in data)

async def test_auto_suggest_mappings(client: AsyncClient, test_project, test_data_source, auth_headers):
    ds_id = test_data_source.id
    columns = ["ad", "soyad", "tc_kimlik", "dogum_tarihi", "bilinmeyen_kolon"]
    res = await client.post(
        f"/api/v1/projects/{test_project.id}/sources/{ds_id}/mappings/auto-suggest",
        headers=auth_headers,
        json={"columns": columns},
    )
    assert res.status_code == 200
    suggestions = res.json()
    assert len(suggestions) > 0

    target_fields = [s["target_fhir_field"] for s in suggestions]
    assert "name[0].given[0]" in target_fields
    assert "name[0].family" in target_fields
    assert "identifier[0].value" in target_fields
    assert "birthDate" in target_fields


async def test_batch_update_and_list_mappings(
    client: AsyncClient, test_project, test_data_source, auth_headers
):
    # Batch create
    rules = [
        {
            "source_field": "hasta_adi",
            "target_fhir_field": "name[0].given[0]",
            "transformation_type": "direct",
            "transformation_config": None,
        },
        {
            "source_field": "hasta_soyadi",
            "target_fhir_field": "name[0].family",
            "transformation_type": "direct",
            "transformation_config": None,
        },
    ]

    res = await client.post(
        f"/api/v1/projects/{test_project.id}/sources/{test_data_source.id}/mappings/batch",
        headers=auth_headers,
        json={"rules": rules},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["source_field"] == "hasta_adi"

    # List
    res_list = await client.get(
        f"/api/v1/projects/{test_project.id}/sources/{test_data_source.id}/mappings",
        headers=auth_headers,
    )
    assert res_list.status_code == 200
    assert len(res_list.json()) == 2


async def test_preview_mappings(
    client: AsyncClient, test_project, test_data_source_with_preview, auth_headers
):
    ds_id = test_data_source_with_preview.id
    
    # 1. Create a mapping rule
    rules = [
        {
            "source_field": "hasta_adi",
            "target_fhir_field": "name[0].given[0]",
            "transformation_type": "direct",
        },
        {
            "source_field": "hasta_soyadi",
            "target_fhir_field": "name[0].family",
            "transformation_type": "direct",
        },
    ]
    await client.post(
        f"/api/v1/projects/{test_project.id}/sources/{ds_id}/mappings/batch",
        headers=auth_headers,
        json={"rules": rules},
    )

    # 2. Trigger preview
    res = await client.post(
        f"/api/v1/projects/{test_project.id}/sources/{ds_id}/mappings/preview",
        headers=auth_headers,
    )
    assert res.status_code == 200
    fhir_data = res.json()
    assert len(fhir_data) > 0

    first_resource = fhir_data[0]
    assert first_resource["resourceType"] == "Patient"
    assert first_resource["name"][0]["given"][0] == "Ahmet" # Assuming preview data has Ahmet
    assert first_resource["name"][0]["family"] == "Yılmaz"
