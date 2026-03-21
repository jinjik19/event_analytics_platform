"""
E2E tests for GET /api/v1/analytics/* endpoints.

Each test creates a real project in Postgres (via project_repository) to obtain
a valid API key, then hits the analytics endpoint through the ASGI test client.
The ClickHouse DW layer is replaced by the mock_dw_repo fixture defined in conftest.py.
"""

import pytest
from httpx import AsyncClient

from domain.utils.generate_uuid import generate_uuid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE = "/api/v1/analytics"


async def _create_project(project_repository, make_project):
    """Insert a project and return it (for its api_key)."""
    project = make_project()
    await project_repository.add(project)
    return project


# ---------------------------------------------------------------------------
# GET /analytics/events-per-day
# ---------------------------------------------------------------------------


class TestEventsPerDayEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_with_valid_api_key(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/events-per-day",
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_is_list_of_events_per_day(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/events-per-day",
            headers={"X-Api-Key": project.api_key},
        )

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["date"] == "2026-03-01"
        assert data[0]["count"] == 100
        assert data[1]["date"] == "2026-03-02"
        assert data[1]["count"] == 200

    @pytest.mark.asyncio
    async def test_returns_401_with_invalid_api_key(
        self, analytics_client: AsyncClient
    ):
        response = await analytics_client.get(
            f"{BASE}/events-per-day",
            headers={"X-Api-Key": "invalid-key"},
        )

        assert response.status_code == 401
        assert response.json()["code"] == "UnauthorizedError"

    @pytest.mark.asyncio
    async def test_returns_401_without_api_key(self, analytics_client: AsyncClient):
        response = await analytics_client.get(f"{BASE}/events-per-day")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_response_schema_has_required_fields(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/events-per-day",
            headers={"X-Api-Key": project.api_key},
        )

        for item in response.json():
            assert "date" in item
            assert "count" in item


# ---------------------------------------------------------------------------
# GET /analytics/funnel
# ---------------------------------------------------------------------------


class TestFunnelEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_with_default_params(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/funnel",
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_is_list_of_funnel_steps(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/funnel",
            headers={"X-Api-Key": project.api_key},
        )

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4
        assert data[0]["step"] == "page_view"
        assert data[0]["users"] == 1000
        assert data[0]["conversion_from_prev"] is None
        assert data[3]["step"] == "purchase"
        assert data[3]["conversion_from_top"] == 0.15

    @pytest.mark.asyncio
    async def test_response_schema_has_required_fields(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/funnel",
            headers={"X-Api-Key": project.api_key},
        )

        for item in response.json():
            assert "step" in item
            assert "users" in item
            assert "conversion_from_prev" in item
            assert "conversion_from_top" in item

    @pytest.mark.asyncio
    async def test_accepts_custom_query_params(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/funnel",
            params={
                "steps": ["page_view", "purchase"],
                "date_from": "2026-01-01",
                "date_to": "2026-01-31",
                "window_days": 14,
            },
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_422_with_invalid_step(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/funnel",
            params={"steps": ["not_a_real_event_type"]},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_401_with_invalid_api_key(
        self, analytics_client: AsyncClient
    ):
        response = await analytics_client.get(
            f"{BASE}/funnel",
            headers={"X-Api-Key": "bad-key"},
        )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /analytics/top-products
# ---------------------------------------------------------------------------


class TestTopProductsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_with_by_cart_metric(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-products",
            params={"metric": "by_cart"},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_200_with_by_revenue_metric(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-products",
            params={"metric": "by_revenue"},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_is_list_of_products(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-products",
            params={"metric": "by_cart"},
            headers={"X-Api-Key": project.api_key},
        )

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["product_name"] == "Laptop"
        assert data[0]["category"] == "Electronics"
        assert data[0]["revenue"] == 75000.0

    @pytest.mark.asyncio
    async def test_response_schema_has_required_fields(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-products",
            params={"metric": "by_cart"},
            headers={"X-Api-Key": project.api_key},
        )

        for item in response.json():
            assert "category" in item
            assert "product_id" in item
            assert "product_name" in item
            assert "add_to_cart_count" in item
            assert "purchase_count" in item
            assert "revenue" in item

    @pytest.mark.asyncio
    async def test_returns_422_without_metric(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-products",
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_with_invalid_metric(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-products",
            params={"metric": "by_clicks"},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_with_limit_out_of_range(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-products",
            params={"metric": "by_cart", "limit": 0},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_401_with_invalid_api_key(
        self, analytics_client: AsyncClient
    ):
        response = await analytics_client.get(
            f"{BASE}/top-products",
            params={"metric": "by_cart"},
            headers={"X-Api-Key": "bad-key"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_accepts_limit_param(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-products",
            params={"metric": "by_cart", "limit": 5},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /analytics/retention
# ---------------------------------------------------------------------------


class TestRetentionEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_with_default_params(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/retention",
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_is_list_of_cohort_rows(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/retention",
            headers={"X-Api-Key": project.api_key},
        )

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["day_number"] == 0
        assert data[0]["retention_pct"] == 100.0
        assert data[1]["day_number"] == 7

    @pytest.mark.asyncio
    async def test_response_schema_has_required_fields(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/retention",
            headers={"X-Api-Key": project.api_key},
        )

        for item in response.json():
            assert "cohort_date" in item
            assert "day_number" in item
            assert "retained_users" in item
            assert "cohort_size" in item
            assert "retention_pct" in item

    @pytest.mark.asyncio
    async def test_accepts_custom_days(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/retention",
            params={"days": 7},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_422_with_days_out_of_range(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/retention",
            params={"days": 366},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_with_negative_days(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/retention",
            params={"days": -1},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_401_with_invalid_api_key(
        self, analytics_client: AsyncClient
    ):
        response = await analytics_client.get(
            f"{BASE}/retention",
            headers={"X-Api-Key": "bad-key"},
        )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /analytics/top-countries
# ---------------------------------------------------------------------------


class TestTopCountriesEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_with_default_params(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_is_list_of_countries(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            headers={"X-Api-Key": project.api_key},
        )

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["country"] == "US"
        assert data[0]["unique_users"] == 5000
        assert data[0]["revenue"] == 150000.0

    @pytest.mark.asyncio
    async def test_response_schema_has_required_fields(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            headers={"X-Api-Key": project.api_key},
        )

        for item in response.json():
            assert "country" in item
            assert "unique_users" in item
            assert "events_count" in item
            assert "revenue" in item

    @pytest.mark.asyncio
    async def test_accepts_sort_by_events(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            params={"sort_by": "by_events"},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_accepts_sort_by_revenue(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            params={"sort_by": "by_revenue"},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_422_with_invalid_sort_by(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            params={"sort_by": "by_name"},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_with_limit_exceeds_max(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            params={"limit": 999},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_401_with_invalid_api_key(
        self, analytics_client: AsyncClient
    ):
        response = await analytics_client.get(
            f"{BASE}/top-countries",
            headers={"X-Api-Key": "bad-key"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_accepts_limit_param(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            params={"limit": 5},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_accepts_custom_date_range(
        self, analytics_client: AsyncClient, project_repository, make_project
    ):
        project = await _create_project(project_repository, make_project)

        response = await analytics_client.get(
            f"{BASE}/top-countries",
            params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
            headers={"X-Api-Key": project.api_key},
        )

        assert response.status_code == 200
