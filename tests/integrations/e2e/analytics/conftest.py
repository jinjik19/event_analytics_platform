from datetime import date
from typing import AsyncGenerator, AsyncIterable
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from dishka import Provider, Scope, provide
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from structlog import get_logger

from domain.cache.repository import Cache
from domain.event.consumer import EventConsumer
from domain.event.producer import EventProducer
from domain.event.repository import (
    EventCountByDay,
    EventFunnelResult,
    EventRetentionResult,
    EventTopCountriesResult,
    EventTopProductsResult,
    IEventAnalyticsRepository,
)
from domain.event.types import AnalyticsMetrics, CountriesMetrics, EventType
from entrypoint.api.main import create_app
from infrastructure.cache.redis import RedisCache
from infrastructure.config.settings import Settings
from infrastructure.di.providers.types import CacheRedis, StreamRedis
from infrastructure.stream.redis_consumer import RedisEventConsumer
from infrastructure.stream.redis_producer import RedisEventProducer


# ---------------------------------------------------------------------------
# Default stub data returned by the mock DW repository
# ---------------------------------------------------------------------------

STUB_EVENTS_PER_DAY = [
    EventCountByDay(date=date(2026, 3, 1), count=100),
    EventCountByDay(date=date(2026, 3, 2), count=200),
]

STUB_FUNNEL = [
    EventFunnelResult(
        step=EventType.PAGE_VIEW,
        users=1000,
        conversion_from_prev=None,
        conversion_from_top=None,
    ),
    EventFunnelResult(
        step=EventType.PRODUCT_VIEW,
        users=600,
        conversion_from_prev=0.6,
        conversion_from_top=0.6,
    ),
    EventFunnelResult(
        step=EventType.ADD_TO_CART,
        users=300,
        conversion_from_prev=0.5,
        conversion_from_top=0.3,
    ),
    EventFunnelResult(
        step=EventType.PURCHASE,
        users=150,
        conversion_from_prev=0.5,
        conversion_from_top=0.15,
    ),
]

STUB_TOP_PRODUCTS = [
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

STUB_RETENTION = [
    EventRetentionResult(
        cohort_date=date(2026, 1, 1),
        day_number=0,
        retained_users=500,
        cohort_size=500,
        retention_pct=100.0,
    ),
    EventRetentionResult(
        cohort_date=date(2026, 1, 1),
        day_number=7,
        retained_users=200,
        cohort_size=500,
        retention_pct=40.0,
    ),
]

STUB_TOP_COUNTRIES = [
    EventTopCountriesResult(
        country="US",
        unique_users=5000,
        events_count=25000,
        revenue=150000.0,
    ),
    EventTopCountriesResult(
        country="DE",
        unique_users=2000,
        events_count=8000,
        revenue=60000.0,
    ),
]


# ---------------------------------------------------------------------------
# Mock DW analytics repository
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_dw_repo():
    """AsyncMock implementing IEventAnalyticsRepository with stub data."""
    repo = AsyncMock(spec=IEventAnalyticsRepository)
    repo.count_event_by_day = AsyncMock(return_value=STUB_EVENTS_PER_DAY)
    repo.funnel = AsyncMock(return_value=STUB_FUNNEL)
    repo.top_products = AsyncMock(return_value=STUB_TOP_PRODUCTS)
    repo.retention = AsyncMock(return_value=STUB_RETENTION)
    repo.top_countries = AsyncMock(return_value=STUB_TOP_COUNTRIES)
    return repo


# ---------------------------------------------------------------------------
# App fixture with mocked DW + other infrastructure providers
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def analytics_app(
    apply_migrations,
    db_settings: Settings,
    fake_redis_client,
    fake_stream_redis,
    mock_dw_repo,
) -> AsyncGenerator[FastAPI, None]:
    class TestSettingsProvider(Provider):
        @provide(scope=Scope.APP)
        def get_settings(self) -> Settings:
            return db_settings

    class TestCacheProvider(Provider):
        scope = Scope.APP

        @provide
        async def get_client(self) -> AsyncIterable[CacheRedis]:
            yield fake_redis_client

        @provide
        def get_cache(self, client: CacheRedis) -> Cache:
            return RedisCache(client)

    class TestStreamProvider(Provider):
        scope = Scope.APP

        @provide
        async def get_client(self) -> AsyncIterable[StreamRedis]:
            yield fake_stream_redis

        @provide
        def get_producer(self, client: StreamRedis) -> EventProducer:
            return RedisEventProducer(client)

        @provide
        def get_consumer(self, client: StreamRedis) -> EventConsumer:
            return RedisEventConsumer(
                redis=client,
                logger=get_logger(),
                group_name="test_group",
                consumer_name="test_worker",
            )

    class TestDWProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_event_analytics_repo(self) -> IEventAnalyticsRepository:
            return mock_dw_repo

    with (
        patch("entrypoint.api.main.SettingsProvider", return_value=TestSettingsProvider()),
        patch("entrypoint.api.main.CacheProvider", return_value=TestCacheProvider()),
        patch("entrypoint.api.main.StreamProvider", return_value=TestStreamProvider()),
        patch("entrypoint.api.main.DWProvider", return_value=TestDWProvider()),
    ):
        _app = create_app()
        yield _app


@pytest_asyncio.fixture
async def analytics_client(analytics_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=analytics_app), base_url="http://test"
    ) as ac:
        yield ac
