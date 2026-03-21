from datetime import date
from unittest.mock import AsyncMock, call

import pytest

from application.event.schemas.events_per_day import EventsPerDayResponseDTO
from application.event.services.analytics.event_per_day import EventsPerDayService
from domain.cache.repository import EVENTS_PER_DAY_TTL
from domain.event.repository import EventCountByDay, IEventAnalyticsRepository
from domain.utils.generate_uuid import generate_uuid


@pytest.fixture
def mock_analytics_repo():
    repo = AsyncMock(spec=IEventAnalyticsRepository)
    repo.count_event_by_day = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_analytics_repo, mock_logger, mock_cache):
    return EventsPerDayService(
        event_dw=mock_analytics_repo,
        logger=mock_logger,
        cache=mock_cache,
    )


class TestEventsPerDayService:
    async def test_returns_dtos_from_repo_on_cache_miss(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_analytics_repo.count_event_by_day.return_value = [
            EventCountByDay(date=date(2026, 3, 1), count=100),
            EventCountByDay(date=date(2026, 3, 2), count=200),
        ]

        result = await service(project_id=project_id)

        assert len(result) == 2
        assert all(isinstance(r, EventsPerDayResponseDTO) for r in result)
        assert result[0].date == date(2026, 3, 1)
        assert result[0].count == 100
        assert result[1].date == date(2026, 3, 2)
        assert result[1].count == 200

    async def test_calls_repo_with_correct_project_id(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()

        await service(project_id=project_id)

        mock_analytics_repo.count_event_by_day.assert_called_once_with(project_id)

    async def test_does_not_call_repo_on_cache_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [{"date": "2026-03-01", "count": 77}]

        await service(project_id=project_id)

        mock_analytics_repo.count_event_by_day.assert_not_called()

    async def test_returns_dtos_from_cache_on_cache_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {"date": "2026-03-01", "count": 77},
            {"date": "2026-03-02", "count": 88},
        ]

        result = await service(project_id=project_id)

        assert len(result) == 2
        assert all(isinstance(r, EventsPerDayResponseDTO) for r in result)
        assert result[0].count == 77
        assert result[1].count == 88

    async def test_does_not_write_cache_on_cache_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [{"date": "2026-03-01", "count": 1}]

        await service(project_id=project_id)

        mock_cache.set.assert_not_called()

    async def test_writes_result_to_cache_after_repo_call(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_analytics_repo.count_event_by_day.return_value = [
            EventCountByDay(date=date(2026, 3, 1), count=50),
        ]

        await service(project_id=project_id)

        mock_cache.set.assert_called_once()

    async def test_uses_correct_cache_key(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()

        await service(project_id=project_id)

        expected_key = f"analytics:events_per_day:{project_id}"
        mock_cache.get.assert_called_once_with(expected_key)

    async def test_caches_with_correct_ttl(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_analytics_repo.count_event_by_day.return_value = [
            EventCountByDay(date=date(2026, 3, 1), count=10),
        ]

        await service(project_id=project_id)

        set_call = mock_cache.set.call_args
        assert set_call.kwargs["ttl"] == EVENTS_PER_DAY_TTL

    async def test_caches_serialized_json_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_analytics_repo.count_event_by_day.return_value = [
            EventCountByDay(date=date(2026, 3, 15), count=42),
        ]

        await service(project_id=project_id)

        cached_value = mock_cache.set.call_args.args[1]
        assert isinstance(cached_value, list)
        assert cached_value[0]["date"] == "2026-03-15"
        assert cached_value[0]["count"] == 42

    async def test_returns_empty_list_when_repo_returns_empty(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_analytics_repo.count_event_by_day.return_value = []

        result = await service(project_id=project_id)

        assert result == []

    async def test_still_caches_when_repo_returns_empty(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_analytics_repo.count_event_by_day.return_value = []

        await service(project_id=project_id)

        mock_cache.set.assert_called_once()
        assert mock_cache.set.call_args.args[1] == []

    async def test_logs_info_on_call(self, service, mock_analytics_repo, mock_logger):
        project_id = generate_uuid()

        await service(project_id=project_id)

        mock_logger.info.assert_called_once()

    async def test_different_project_ids_use_different_cache_keys(
        self, mock_analytics_repo, mock_logger, mock_cache
    ):
        project_id_1 = generate_uuid()
        project_id_2 = generate_uuid()
        svc = EventsPerDayService(
            event_dw=mock_analytics_repo, logger=mock_logger, cache=mock_cache
        )

        await svc(project_id=project_id_1)
        await svc(project_id=project_id_2)

        get_calls = mock_cache.get.call_args_list
        keys = [c.args[0] for c in get_calls]
        assert keys[0] != keys[1]
        assert str(project_id_1) in keys[0]
        assert str(project_id_2) in keys[1]
