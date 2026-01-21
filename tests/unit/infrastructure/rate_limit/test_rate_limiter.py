import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request, Response

from infrastructure.rate_limit.dependencies import PlanBasedRateLimiter, IPRateLimiter
from domain.exceptions.app import RateLimitExceededError
from domain.project.types import Plan

@pytest.fixture
def mock_deps():
    settings = MagicMock()
    settings.is_rate_limit_enabled = True
    settings.app_env = "test"
    settings.rate_limit_no_auth_rpm = 5
    settings.rate_limit_free_rpm = 10
    settings.rate_limit_project_create_rpm = 2

    uow = AsyncMock()
    cache = AsyncMock()

    return settings, uow, cache

@pytest.mark.asyncio
async def test_plan_limiter_no_api_key(mock_deps):
    settings, uow, cache = mock_deps
    limiter_cls = PlanBasedRateLimiter(settings, uow, cache)

    request = MagicMock(spec=Request)
    request.headers.get.return_value = None
    request.client.host = "127.0.0.1"

    ident, rpm = await limiter_cls._get_identifier_and_rpm(None, request)

    assert ident == "ip:127.0.0.1"
    assert rpm == 5 # rate_limit_no_auth_rpm

@pytest.mark.asyncio
async def test_plan_limiter_cache_hit(mock_deps):
    settings, uow, cache = mock_deps
    limiter_cls = PlanBasedRateLimiter(settings, uow, cache)

    api_key = "wk_test_123"
    project_id = "proj_abc"

    request = MagicMock(spec=Request)
    cache.get.return_value = project_id

    project_mock = MagicMock()
    project_mock.project_id = project_id
    project_mock.plan = Plan.FREE
    uow.project.get_by_id.return_value = project_mock

    ident, rpm = await limiter_cls._get_identifier_and_rpm(api_key, request)

    assert ident == f"project:{project_id}"
    assert rpm == 10 # rate_limit_free_rpm
    cache.get.assert_awaited_with(f"api_key:{api_key}")

@pytest.mark.asyncio
async def test_plan_limiter_db_fallback(mock_deps):
    settings, uow, cache = mock_deps
    limiter_cls = PlanBasedRateLimiter(settings, uow, cache)

    api_key = "wk_test_123"
    request = MagicMock(spec=Request)

    cache.get.return_value = None

    project_mock = MagicMock()
    project_mock.project_id = "proj_db"
    project_mock.plan = Plan.FREE
    uow.project.get_by_api_key.return_value = project_mock

    ident, rpm = await limiter_cls._get_identifier_and_rpm(api_key, request)

    assert ident == "project:proj_db"
    cache.set.assert_awaited_with(api_key, "proj_db")
