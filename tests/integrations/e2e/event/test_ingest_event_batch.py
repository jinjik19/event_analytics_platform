from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from domain.utils.generate_uuid import generate_uuid


@pytest.mark.asyncio
async def test_ingest_event_batch_success(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {
        "events": [
            {
                "user_id": str(generate_uuid()),
                "session_id": str(generate_uuid()),
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {
                    "page_url": "http://test.com/page1",
                    "country": "US",
                    "browser": "Chrome",
                },
            },
            {
                "user_id": str(generate_uuid()),
                "session_id": str(generate_uuid()),
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {
                    "page_url": "http://test.com/page2",
                    "country": "NZ",
                    "browser": "Firefox",
                },
            },
        ]
    }

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    assert data["status"] == "accepted"
    assert len(data["event_ids"]) == 2
    assert all(isinstance(eid, str) for eid in data["event_ids"])


@pytest.mark.asyncio
async def test_ingest_event_batch_filters_invalid_events(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {
        "events": [
            {
                "user_id": str(generate_uuid()),
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"page_url": "http://test.com/valid"},
            },
            {
                "event_type": "invalid_event_type",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {},
            },
            {
                "event_type": "purchase",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {},
            },
        ]
    }

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    assert data["status"] == "accepted"
    assert len(data["event_ids"]) == 1


@pytest.mark.asyncio
async def test_ingest_event_batch_empty_after_filtering(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {
        "events": [
            {
                "event_type": "invalid_type",
                "timestamp": "invalid",
                "properties": {},
            },
        ]
    }

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    assert data["status"] == "accepted"
    assert len(data["event_ids"]) == 0


@pytest.mark.asyncio
async def test_ingest_event_batch_with_purchase_events(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {
        "events": [
            {
                "user_id": str(generate_uuid()),
                "session_id": str(generate_uuid()),
                "event_type": "purchase",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {
                    "product_id": "prod_123",
                    "price": 99.99,
                    "quantity": 2,
                    "currency": "USD",
                    "page_url": "http://test.com/checkout",
                },
            },
        ]
    }

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    assert len(data["event_ids"]) == 1


@pytest.mark.asyncio
async def test_ingest_event_batch_mixed_event_types(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {
        "events": [
            {
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"page_url": "http://test.com"},
            },
            {
                "event_type": "product_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"product_id": "prod_1"},
            },
            {
                "event_type": "add_to_cart",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"product_id": "prod_1"},
            },
            {
                "event_type": "remove_from_cart",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"product_id": "prod_1"},
            },
            {
                "event_type": "purchase",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {
                    "product_id": "prod_1",
                    "price": 50.00,
                    "quantity": 1,
                },
            },
        ]
    }

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    assert len(data["event_ids"]) == 5


@pytest.mark.asyncio
async def test_ingest_event_batch_invalid_api_key(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {
        "events": [
            {
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"page_url": "http://test.com"},
            },
        ]
    }

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": "invalid-api-key"}, json=body
    )

    assert response.status_code == 401

    data = response.json()
    assert data["code"] == "UnauthorizedError"


@pytest.mark.asyncio
async def test_ingest_event_batch_missing_api_key(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {
        "events": [
            {
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"page_url": "http://test.com"},
            },
        ]
    }

    response = await client.post("/api/v1/event/batch", json=body)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ingest_event_batch_persists_events(
    client: AsyncClient, project_repository, event_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {
        "events": [
            {
                "user_id": "user_123",
                "session_id": "session_456",
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {
                    "page_url": "http://test.com/persisted",
                    "country": "NZ",
                },
            },
            {
                "user_id": "user_789",
                "event_type": "product_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"product_id": "prod_abc"},
            },
        ]
    }

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    event_ids = data["event_ids"]

    events = await event_repository.get_by_project_id(
        project_id=project.project_id, limit=10, offset=0
    )
    assert len(events) == 2

    persisted_ids = {str(e.event_id) for e in events}
    assert set(event_ids) == persisted_ids


@pytest.mark.asyncio
async def test_ingest_event_batch_empty_list(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    body = {"events": []}

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    assert data["status"] == "accepted"
    assert len(data["event_ids"]) == 0


@pytest.mark.asyncio
async def test_ingest_event_batch_large_batch(
    client: AsyncClient, project_repository, make_project
):
    project = make_project()
    await project_repository.add(project)

    events = [
        {
            "user_id": f"user_{i}",
            "event_type": "page_view",
            "timestamp": datetime.now(UTC).isoformat(),
            "properties": {"page_url": f"http://test.com/page{i}"},
        }
        for i in range(50)
    ]

    body = {"events": events}

    response = await client.post(
        "/api/v1/event/batch", headers={"X-Api-Key": project.api_key}, json=body
    )

    assert response.status_code == 202

    data = response.json()
    assert len(data["event_ids"]) == 50
