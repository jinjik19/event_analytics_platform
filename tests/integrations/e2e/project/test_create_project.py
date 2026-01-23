import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient, auth_headers: dict[str, str]):
    body = {
        "name": "Test Project",
        "plan": "free",
    }

    response = await client.post("/api/v1/project", json=body, headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == body["name"]
    assert data["plan"] == body["plan"]
    assert "project_id" in data
    assert "api_key" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_project_validation_error(client: AsyncClient, auth_headers: dict[str, str]):
    body = {
        "name": "T",
        "plan": "free",
    }

    response = await client.post("/api/v1/project", json=body, headers=auth_headers)

    assert response.status_code == 422

    data = response.json()
    assert data["code"] == "ValidationError"
