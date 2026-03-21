from datetime import date
from unittest.mock import AsyncMock

import pytest

from application.event.schemas.retention import (
    EventRetentionQueryParams,
    EventRetentionResponseDTO,
)
from application.event.services.analytics.retention import EventRetentionService
from domain.cache.repository import EVENT_HISTORICAL_TTL, EVENT_RETENTION_TTL
from domain.event.repository import (
    EventRetentionParams,
    EventRetentionResult,
    IEventAnalyticsRepository,
)
from domain.utils.generate_uuid import generate_uuid


@pytest.fixture
def mock_analytics_repo():
    repo = AsyncMock(spec=IEventAnalyticsRepository)
    repo.retention = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_analytics_repo, mock_logger, mock_cache):
    return EventRetentionService(
        event_dw=mock_analytics_repo,
        logger=mock_logger,
        cache=mock_cache,
    )


@pytest.fixture
def retention_results():
    return [
        EventRetentionResult(
            cohort_date=date(2026, 1, 1),
            day_number=0,
            retained_users=500,
            cohort_size=500,
            retention_pct=100.0,
        ),
        EventRetentionResult(
            cohort_date=date(2026, 1, 1),
            day_number=1,
            retained_users=350,
            cohort_size=500,
            retention_pct=70.0,
        ),
        EventRetentionResult(
            cohort_date=date(2026, 1, 1),
            day_number=7,
            retained_users=200,
            cohort_size=500,
            retention_pct=40.0,
        ),
    ]


class TestEventRetentionService:
    async def test_returns_dtos_from_repo_on_cache_miss(
        self, service, mock_analytics_repo, mock_cache, retention_results
    ):
        project_id = generate_uuid()
        mock_analytics_repo.retention.return_value = retention_results
        params = EventRetentionQueryParams()

        result = await service(project_id=project_id, params=params)

        assert len(result) == 3
        assert all(isinstance(r, EventRetentionResponseDTO) for r in result)
        assert result[0].day_number == 0
        assert result[0].retention_pct == 100.0
        assert result[1].retention_pct == 70.0
        assert result[2].day_number == 7

    async def test_calls_repo_with_correct_params(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        date_from = date(2026, 1, 1)
        date_to = date(2026, 1, 31)
        params = EventRetentionQueryParams(date_from=date_from, date_to=date_to, days=14)

        await service(project_id=project_id, params=params)

        mock_analytics_repo.retention.assert_called_once()
        call_params: EventRetentionParams = (
            mock_analytics_repo.retention.call_args.kwargs["params"]
        )
        assert call_params.project_id == project_id
        assert call_params.date_from == date_from
        assert call_params.date_to == date_to
        assert call_params.days == 14

    async def test_returns_dtos_from_cache_on_cache_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {
                "cohort_date": "2026-01-01",
                "day_number": 7,
                "retained_users": 100,
                "cohort_size": 400,
                "retention_pct": 25.0,
            }
        ]

        result = await service(project_id=project_id, params=EventRetentionQueryParams())

        assert len(result) == 1
        assert result[0].day_number == 7
        assert result[0].retention_pct == 25.0
        mock_analytics_repo.retention.assert_not_called()

    async def test_does_not_write_cache_on_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {
                "cohort_date": "2026-01-01",
                "day_number": 0,
                "retained_users": 10,
                "cohort_size": 10,
                "retention_pct": 100.0,
            }
        ]

        await service(project_id=project_id, params=EventRetentionQueryParams())

        mock_cache.set.assert_not_called()

    async def test_uses_retention_ttl_for_recent_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventRetentionQueryParams(date_to=date.today())

        await service(project_id=project_id, params=params)

        assert mock_cache.set.call_args.kwargs["ttl"] == EVENT_RETENTION_TTL

    async def test_uses_historical_ttl_for_past_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventRetentionQueryParams(
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 31),
        )

        await service(project_id=project_id, params=params)

        assert mock_cache.set.call_args.kwargs["ttl"] == EVENT_HISTORICAL_TTL

    async def test_cache_key_includes_project_id_and_dates_and_days(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        date_from = date(2026, 2, 1)
        date_to = date(2026, 2, 28)
        params = EventRetentionQueryParams(date_from=date_from, date_to=date_to, days=7)

        await service(project_id=project_id, params=params)

        cache_key = mock_cache.get.call_args.args[0]
        assert str(project_id) in cache_key
        assert str(date_from) in cache_key
        assert str(date_to) in cache_key
        assert "7" in cache_key

    async def test_different_days_produce_different_cache_keys(
        self, mock_analytics_repo, mock_logger, mock_cache
    ):
        project_id = generate_uuid()
        svc = EventRetentionService(
            event_dw=mock_analytics_repo, logger=mock_logger, cache=mock_cache
        )

        await svc(project_id=project_id, params=EventRetentionQueryParams(days=7))
        await svc(project_id=project_id, params=EventRetentionQueryParams(days=30))

        keys = [c.args[0] for c in mock_cache.get.call_args_list]
        assert keys[0] != keys[1]

    async def test_caches_serialized_json_data(
        self, service, mock_analytics_repo, mock_cache, retention_results
    ):
        project_id = generate_uuid()
        mock_analytics_repo.retention.return_value = retention_results[:1]

        await service(project_id=project_id, params=EventRetentionQueryParams())

        cached_value = mock_cache.set.call_args.args[1]
        assert isinstance(cached_value, list)
        assert cached_value[0]["cohort_date"] == "2026-01-01"
        assert cached_value[0]["retention_pct"] == 100.0

    async def test_returns_empty_list_when_repo_empty(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()

        result = await service(project_id=project_id, params=EventRetentionQueryParams())

        assert result == []

    async def test_logs_info_on_call(self, service, mock_analytics_repo, mock_logger):
        project_id = generate_uuid()

        await service(project_id=project_id, params=EventRetentionQueryParams())

        mock_logger.info.assert_called_once()
