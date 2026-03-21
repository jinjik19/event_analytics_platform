from datetime import date
from unittest.mock import AsyncMock

import pytest

from application.event.schemas.top_products import (
    EventTopProductsQueryParams,
    EventTopProductsResponseDTO,
)
from application.event.services.analytics.top_products import EventTopProductsService
from domain.cache.repository import EVENT_HISTORICAL_TTL, EVENT_TOP_PRODUCTS_TTL
from domain.event.repository import (
    EventTopProductsParams,
    EventTopProductsResult,
    IEventAnalyticsRepository,
)
from domain.event.types import AnalyticsMetrics
from domain.utils.generate_uuid import generate_uuid


@pytest.fixture
def mock_analytics_repo():
    repo = AsyncMock(spec=IEventAnalyticsRepository)
    repo.top_products = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_analytics_repo, mock_logger, mock_cache):
    return EventTopProductsService(
        event_dw=mock_analytics_repo,
        logger=mock_logger,
        cache=mock_cache,
    )


@pytest.fixture
def top_products_results():
    return [
        EventTopProductsResult(
            category="Electronics",
            product_id="prod-001",
            product_name="Laptop",
            add_to_cart_count=300,
            purchase_count=150,
            revenue=75000.0,
        ),
        EventTopProductsResult(
            category="Books",
            product_id="book-001",
            product_name="Clean Code",
            add_to_cart_count=100,
            purchase_count=80,
            revenue=2400.0,
        ),
    ]


class TestEventTopProductsService:
    async def test_returns_dtos_from_repo_on_cache_miss(
        self, service, mock_analytics_repo, mock_cache, top_products_results
    ):
        project_id = generate_uuid()
        mock_analytics_repo.top_products.return_value = top_products_results
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART)

        result = await service(project_id=project_id, params=params)

        assert len(result) == 2
        assert all(isinstance(r, EventTopProductsResponseDTO) for r in result)
        assert result[0].product_name == "Laptop"
        assert result[0].category == "Electronics"
        assert result[0].revenue == 75000.0
        assert result[1].product_id == "book-001"

    async def test_calls_repo_with_correct_params(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        date_from = date(2026, 1, 1)
        date_to = date(2026, 1, 31)
        params = EventTopProductsQueryParams(
            metric=AnalyticsMetrics.BY_REVENUE,
            date_from=date_from,
            date_to=date_to,
            limit=5,
        )

        await service(project_id=project_id, params=params)

        mock_analytics_repo.top_products.assert_called_once()
        call_params: EventTopProductsParams = (
            mock_analytics_repo.top_products.call_args.kwargs["params"]
        )
        assert call_params.project_id == project_id
        assert call_params.metric == AnalyticsMetrics.BY_REVENUE
        assert call_params.date_from == date_from
        assert call_params.date_to == date_to
        assert call_params.limit == 5

    async def test_returns_from_cache_on_cache_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {
                "category": "Toys",
                "product_id": "toy-01",
                "product_name": "LEGO",
                "add_to_cart_count": 50,
                "purchase_count": 30,
                "revenue": 900.0,
            }
        ]

        result = await service(
            project_id=project_id,
            params=EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART),
        )

        assert len(result) == 1
        assert result[0].product_name == "LEGO"
        mock_analytics_repo.top_products.assert_not_called()

    async def test_does_not_write_cache_on_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {
                "category": "X",
                "product_id": "x-01",
                "product_name": "X",
                "add_to_cart_count": 1,
                "purchase_count": 1,
                "revenue": 1.0,
            }
        ]

        await service(
            project_id=project_id,
            params=EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART),
        )

        mock_cache.set.assert_not_called()

    async def test_uses_top_products_ttl_for_recent_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventTopProductsQueryParams(
            metric=AnalyticsMetrics.BY_CART, date_to=date.today()
        )

        await service(project_id=project_id, params=params)

        assert mock_cache.set.call_args.kwargs["ttl"] == EVENT_TOP_PRODUCTS_TTL

    async def test_uses_historical_ttl_for_past_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventTopProductsQueryParams(
            metric=AnalyticsMetrics.BY_REVENUE,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 12, 31),
        )

        await service(project_id=project_id, params=params)

        assert mock_cache.set.call_args.kwargs["ttl"] == EVENT_HISTORICAL_TTL

    async def test_cache_key_includes_metric(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_REVENUE)

        await service(project_id=project_id, params=params)

        cache_key = mock_cache.get.call_args.args[0]
        assert "by_revenue" in cache_key

    async def test_cache_key_includes_limit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART, limit=25)

        await service(project_id=project_id, params=params)

        cache_key = mock_cache.get.call_args.args[0]
        assert "25" in cache_key

    async def test_cache_key_includes_project_id(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()

        await service(
            project_id=project_id,
            params=EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART),
        )

        cache_key = mock_cache.get.call_args.args[0]
        assert str(project_id) in cache_key

    async def test_different_metrics_produce_different_cache_keys(
        self, mock_analytics_repo, mock_logger, mock_cache
    ):
        project_id = generate_uuid()
        svc = EventTopProductsService(
            event_dw=mock_analytics_repo, logger=mock_logger, cache=mock_cache
        )
        params_cart = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART)
        params_revenue = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_REVENUE)

        await svc(project_id=project_id, params=params_cart)
        await svc(project_id=project_id, params=params_revenue)

        keys = [c.args[0] for c in mock_cache.get.call_args_list]
        assert keys[0] != keys[1]

    async def test_returns_empty_list_when_repo_empty(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()

        result = await service(
            project_id=project_id,
            params=EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART),
        )

        assert result == []

    async def test_logs_info_on_call(self, service, mock_analytics_repo, mock_logger):
        project_id = generate_uuid()

        await service(
            project_id=project_id,
            params=EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART),
        )

        mock_logger.info.assert_called_once()
