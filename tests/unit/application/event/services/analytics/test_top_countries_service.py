from datetime import date
from unittest.mock import AsyncMock

import pytest

from application.event.schemas.top_countries import (
    EventTopCountriesQueryParams,
    EventTopCountriesResponseDTO,
)
from application.event.services.analytics.top_countries import EventTopCountriesService
from domain.cache.repository import EVENT_HISTORICAL_TTL, EVENT_TOP_COUNTRIES_TTL
from domain.event.repository import (
    EventTopCountriesParams,
    EventTopCountriesResult,
    IEventAnalyticsRepository,
)
from domain.event.types import CountriesMetrics
from domain.utils.generate_uuid import generate_uuid


@pytest.fixture
def mock_analytics_repo():
    repo = AsyncMock(spec=IEventAnalyticsRepository)
    repo.top_countries = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_analytics_repo, mock_logger, mock_cache):
    return EventTopCountriesService(
        event_dw=mock_analytics_repo,
        logger=mock_logger,
        cache=mock_cache,
    )


@pytest.fixture
def top_countries_results():
    return [
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
        EventTopCountriesResult(
            country="NZ",
            unique_users=300,
            events_count=1200,
            revenue=9000.0,
        ),
    ]


class TestEventTopCountriesService:
    async def test_returns_dtos_from_repo_on_cache_miss(
        self, service, mock_analytics_repo, mock_cache, top_countries_results
    ):
        project_id = generate_uuid()
        mock_analytics_repo.top_countries.return_value = top_countries_results
        params = EventTopCountriesQueryParams()

        result = await service(project_id=project_id, params=params)

        assert len(result) == 3
        assert all(isinstance(r, EventTopCountriesResponseDTO) for r in result)
        assert result[0].country == "US"
        assert result[0].unique_users == 5000
        assert result[0].revenue == 150000.0
        assert result[2].country == "NZ"

    async def test_calls_repo_with_correct_params(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        date_from = date(2026, 1, 1)
        date_to = date(2026, 1, 31)
        params = EventTopCountriesQueryParams(
            date_from=date_from,
            date_to=date_to,
            limit=5,
            sort_by=CountriesMetrics.BY_REVENUE,
        )

        await service(project_id=project_id, params=params)

        mock_analytics_repo.top_countries.assert_called_once()
        call_params: EventTopCountriesParams = (
            mock_analytics_repo.top_countries.call_args.kwargs["params"]
        )
        assert call_params.project_id == project_id
        assert call_params.date_from == date_from
        assert call_params.date_to == date_to
        assert call_params.limit == 5
        assert call_params.sort_by == CountriesMetrics.BY_REVENUE

    async def test_returns_dtos_from_cache_on_cache_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {
                "country": "AU",
                "unique_users": 100,
                "events_count": 500,
                "revenue": 3000.0,
            }
        ]

        result = await service(project_id=project_id, params=EventTopCountriesQueryParams())

        assert len(result) == 1
        assert result[0].country == "AU"
        mock_analytics_repo.top_countries.assert_not_called()

    async def test_does_not_write_cache_on_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {
                "country": "JP",
                "unique_users": 50,
                "events_count": 200,
                "revenue": 1000.0,
            }
        ]

        await service(project_id=project_id, params=EventTopCountriesQueryParams())

        mock_cache.set.assert_not_called()

    async def test_uses_top_countries_ttl_for_recent_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventTopCountriesQueryParams(date_to=date.today())

        await service(project_id=project_id, params=params)

        assert mock_cache.set.call_args.kwargs["ttl"] == EVENT_TOP_COUNTRIES_TTL

    async def test_uses_historical_ttl_for_past_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventTopCountriesQueryParams(
            date_from=date(2025, 1, 1),
            date_to=date(2025, 12, 31),
        )

        await service(project_id=project_id, params=params)

        assert mock_cache.set.call_args.kwargs["ttl"] == EVENT_HISTORICAL_TTL

    async def test_cache_key_includes_sort_by(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventTopCountriesQueryParams(sort_by=CountriesMetrics.BY_EVENTS)

        await service(project_id=project_id, params=params)

        cache_key = mock_cache.get.call_args.args[0]
        assert "by_events" in cache_key

    async def test_cache_key_includes_limit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventTopCountriesQueryParams(limit=20)

        await service(project_id=project_id, params=params)

        cache_key = mock_cache.get.call_args.args[0]
        assert "20" in cache_key

    async def test_cache_key_includes_project_id(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()

        await service(project_id=project_id, params=EventTopCountriesQueryParams())

        cache_key = mock_cache.get.call_args.args[0]
        assert str(project_id) in cache_key

    async def test_different_sort_by_produce_different_cache_keys(
        self, mock_analytics_repo, mock_logger, mock_cache
    ):
        project_id = generate_uuid()
        svc = EventTopCountriesService(
            event_dw=mock_analytics_repo, logger=mock_logger, cache=mock_cache
        )

        await svc(
            project_id=project_id,
            params=EventTopCountriesQueryParams(sort_by=CountriesMetrics.BY_USERS),
        )
        await svc(
            project_id=project_id,
            params=EventTopCountriesQueryParams(sort_by=CountriesMetrics.BY_REVENUE),
        )

        keys = [c.args[0] for c in mock_cache.get.call_args_list]
        assert keys[0] != keys[1]

    async def test_caches_serialized_json_data(
        self, service, mock_analytics_repo, mock_cache, top_countries_results
    ):
        project_id = generate_uuid()
        mock_analytics_repo.top_countries.return_value = top_countries_results[:1]

        await service(project_id=project_id, params=EventTopCountriesQueryParams())

        cached_value = mock_cache.set.call_args.args[1]
        assert isinstance(cached_value, list)
        assert cached_value[0]["country"] == "US"
        assert cached_value[0]["unique_users"] == 5000

    async def test_returns_empty_list_when_repo_empty(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()

        result = await service(project_id=project_id, params=EventTopCountriesQueryParams())

        assert result == []

    async def test_logs_info_on_call(self, service, mock_analytics_repo, mock_logger):
        project_id = generate_uuid()

        await service(project_id=project_id, params=EventTopCountriesQueryParams())

        mock_logger.info.assert_called_once()
