from httpx import AsyncClient


PROJECT_BODY = {"name": "Test Project", "plan": "free"}


async def test_valid_token_allows_request(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.post(
        "/api/v1/project", json=PROJECT_BODY, headers=auth_headers
    )

    assert response.status_code == 200


async def test_missing_auth_header_returns_403(client: AsyncClient):
    response = await client.post("/api/v1/project", json=PROJECT_BODY)

    assert response.status_code == 403
    assert response.json()["message"] == "Missing Authorization header"


async def test_empty_auth_header_returns_403(client: AsyncClient):
    response = await client.post(
        "/api/v1/project", json=PROJECT_BODY, headers={"Authorization": ""}
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Invalid authorization header format"


async def test_invalid_token_returns_403(client: AsyncClient):
    response = await client.post(
        "/api/v1/project",
        json=PROJECT_BODY,
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Invalid secret token"


async def test_missing_bearer_prefix_returns_403(client: AsyncClient):
    response = await client.post(
        "/api/v1/project",
        json=PROJECT_BODY,
        headers={"Authorization": "Token some-token"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Invalid authorization header format"


async def test_basic_auth_returns_403(client: AsyncClient):
    response = await client.post(
        "/api/v1/project",
        json=PROJECT_BODY,
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Invalid authorization header format"


async def test_bearer_lowercase_returns_403(client: AsyncClient):
    response = await client.post(
        "/api/v1/project",
        json=PROJECT_BODY,
        headers={"Authorization": "bearer valid-token"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Invalid authorization header format"


async def test_bearer_no_space_returns_403(client: AsyncClient):
    response = await client.post(
        "/api/v1/project",
        json=PROJECT_BODY,
        headers={"Authorization": "Bearertoken"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Invalid authorization header format"


async def test_token_with_extra_whitespace_returns_403(client: AsyncClient):
    response = await client.post(
        "/api/v1/project",
        json=PROJECT_BODY,
        headers={"Authorization": "Bearer  extra-space-token"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "Invalid secret token"
