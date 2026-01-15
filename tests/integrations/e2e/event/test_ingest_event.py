from datetime import datetime
import pytest
from httpx import AsyncClient

from domain.utils.generate_uuid import generate_uuid

@pytest.mark.asyncio
async def test_ingest_event_success(client: AsyncClient, project_repository, make_project):
    project = make_project()
    await project_repository.add(project)
    app = client._transport.app

    body = {
        "user_id": str(generate_uuid()),
        "session_id": str(generate_uuid()),
        "event_type": "click",
        "timestamp": datetime.now().isoformat(),
        "properties": {
            "page_url": "http://test.com/page"
        },
        "user_properties": {
            "country": "NZ",
        },
        "device": {
            "browser": "Chrome",
            "os": "Windows",
        },
    }

    response = await client.post(
        "/api/v1/event", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    assert data["event_id"] is not None
    assert data["status"] == "accepted"


@pytest.mark.asyncio
async def test_ingest_event_validation_error(client: AsyncClient, project_repository, make_project):
    project = make_project()
    await project_repository.add(project)
    app = client._transport.app

    body = {
        "user_id": str(generate_uuid()),
        "session_id": str(generate_uuid()),
        "event_type": "click",
        "timestamp": datetime.now().isoformat(),
    }

    response = await client.post(
        "/api/v1/event", headers={"X-Api-Key": str(project.api_key)}, json=body
    )

    assert response.status_code == 422

    data = response.json()
    assert data["code"] == "ValidationError"


@pytest.mark.asyncio
async def test_ingest_event_invalid_api_key(client: AsyncClient, project_repository, make_project):
    project = make_project()
    await project_repository.add(project)
    app = client._transport.app

    body = {
        "user_id": str(generate_uuid()),
        "session_id": str(generate_uuid()),
        "event_type": "click",
        "timestamp": datetime.now().isoformat(),
        "properties": {
            "page_url": "http://test.com/page"
        },
        "user_properties": {
            "country": "NZ",
        },
        "device": {
            "browser": "Chrome",
            "os": "Windows",
        },
    }

    response = await client.post(
        "/api/v1/event", headers={"X-Api-Key": "invalid-api-key"}, json=body
    )
    print(response)

    assert response.status_code == 401

    data = response.json()
    assert data["code"] == "UnauthorizedError"
