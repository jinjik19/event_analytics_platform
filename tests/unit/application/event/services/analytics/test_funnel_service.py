from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from application.event.schemas.funnel import EventFunnelQueryParams, EventFunnelResponseDTO
from application.event.services.analytics.funnel import EventFunnelService
from domain.cache.repository import EVENT_FUNNEL_TTL, EVENT_HISTORICAL_TTL
from domain.event.repository import EventFunnelParams, EventFunnelResult, IEventAnalyticsRepository
from domain.event.types import EventType
from domain.utils.generate_uuid import generate_uuid


@pytest.fixture
def mock_analytics_repo():
    repo = AsyncMock(spec=IEventAnalyticsRepository)
    repo.funnel = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_analytics_repo, mock_logger, mock_cache):
    return EventFunnelService(
        event_dw=mock_analytics_repo,
        logger=mock_logger,
        cache=mock_cache,
    )


@pytest.fixture
def funnel_results():
    return [
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


class TestEventFunnelService:
    async def test_returns_dtos_from_repo_on_cache_miss(
        self, service, mock_analytics_repo, mock_cache, funnel_results
    ):
        project_id = generate_uuid()
        mock_analytics_repo.funnel.return_value = funnel_results
        params = EventFunnelQueryParams()

        result = await service(project_id=project_id, params=params)

        assert len(result) == 4
        assert all(isinstance(r, EventFunnelResponseDTO) for r in result)
        assert result[0].step == EventType.PAGE_VIEW
        assert result[0].users == 1000
        assert result[0].conversion_from_prev is None
        assert result[3].conversion_from_top == 0.15

    async def test_calls_repo_with_correct_params(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        date_from = date(2026, 1, 1)
        date_to = date(2026, 1, 31)
        params = EventFunnelQueryParams(
            steps=[EventType.PAGE_VIEW, EventType.PURCHASE],
            date_from=date_from,
            date_to=date_to,
            window_days=14,
        )

        await service(project_id=project_id, params=params)

        mock_analytics_repo.funnel.assert_called_once()
        call_params: EventFunnelParams = mock_analytics_repo.funnel.call_args.kwargs["params"]
        assert call_params.project_id == project_id
        assert call_params.steps == [EventType.PAGE_VIEW, EventType.PURCHASE]
        assert call_params.date_from == date_from
        assert call_params.date_to == date_to
        assert call_params.window_days == 14

    async def test_returns_dtos_from_cache_on_cache_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {
                "step": "page_view",
                "users": 1000,
                "conversion_from_prev": None,
                "conversion_from_top": None,
            }
        ]

        result = await service(project_id=project_id, params=EventFunnelQueryParams())

        assert len(result) == 1
        assert result[0].step == EventType.PAGE_VIEW
        mock_analytics_repo.funnel.assert_not_called()

    async def test_does_not_write_cache_on_cache_hit(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_cache.get.return_value = [
            {
                "step": "page_view",
                "users": 500,
                "conversion_from_prev": None,
                "conversion_from_top": None,
            }
        ]

        await service(project_id=project_id, params=EventFunnelQueryParams())

        mock_cache.set.assert_not_called()

    async def test_uses_event_funnel_ttl_for_recent_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventFunnelQueryParams(date_to=date.today())

        await service(project_id=project_id, params=params)

        set_call = mock_cache.set.call_args
        assert set_call.kwargs["ttl"] == EVENT_FUNNEL_TTL

    async def test_uses_historical_ttl_for_past_data(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventFunnelQueryParams(
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 31),
        )

        await service(project_id=project_id, params=params)

        set_call = mock_cache.set.call_args
        assert set_call.kwargs["ttl"] == EVENT_HISTORICAL_TTL

    async def test_cache_key_includes_steps(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        params = EventFunnelQueryParams(
            steps=[EventType.PAGE_VIEW, EventType.PURCHASE],
        )

        await service(project_id=project_id, params=params)

        cache_key = mock_cache.get.call_args.args[0]
        assert "page_view" in cache_key
        assert "purchase" in cache_key

    async def test_cache_key_includes_dates_and_window(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        date_from = date(2026, 2, 1)
        date_to = date(2026, 2, 28)
        params = EventFunnelQueryParams(
            date_from=date_from, date_to=date_to, window_days=3
        )

        await service(project_id=project_id, params=params)

        cache_key = mock_cache.get.call_args.args[0]
        assert str(date_from) in cache_key
        assert str(date_to) in cache_key
        assert "3" in cache_key

    async def test_cache_key_includes_project_id(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()

        await service(project_id=project_id, params=EventFunnelQueryParams())

        cache_key = mock_cache.get.call_args.args[0]
        assert str(project_id) in cache_key

    async def test_returns_empty_list_when_repo_empty(
        self, service, mock_analytics_repo, mock_cache
    ):
        project_id = generate_uuid()
        mock_analytics_repo.funnel.return_value = []

        result = await service(project_id=project_id, params=EventFunnelQueryParams())

        assert result == []

    async def test_logs_info_on_call(self, service, mock_analytics_repo, mock_logger):
        project_id = generate_uuid()

        await service(project_id=project_id, params=EventFunnelQueryParams())

        mock_logger.info.assert_called_once()

    async def test_different_params_produce_different_cache_keys(
        self, mock_analytics_repo, mock_logger, mock_cache
    ):
        project_id = generate_uuid()
        svc = EventFunnelService(
            event_dw=mock_analytics_repo, logger=mock_logger, cache=mock_cache
        )
        params_a = EventFunnelQueryParams(window_days=7)
        params_b = EventFunnelQueryParams(window_days=14)

        await svc(project_id=project_id, params=params_a)
        await svc(project_id=project_id, params=params_b)

        keys = [c.args[0] for c in mock_cache.get.call_args_list]
        assert keys[0] != keys[1]
