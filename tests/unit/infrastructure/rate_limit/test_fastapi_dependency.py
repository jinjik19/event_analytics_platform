from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.rate_limit.dependencies import IPRateLimiter, PlanBasedRateLimiter
from infrastructure.rate_limit.fastapi_dependency import rate_limit_dependency


def _make_request_with_container(limiter_mock: AsyncMock) -> MagicMock:
    container = AsyncMock()
    container.get = AsyncMock(return_value=limiter_mock)
    request = MagicMock()
    request.state.dishka_container = container
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    return request


def test_returns_callable() -> None:
    dep = rate_limit_dependency(IPRateLimiter)
    assert callable(dep)

def test_returns_different_callables_for_different_types() -> None:
    dep_ip = rate_limit_dependency(IPRateLimiter)
    dep_plan = rate_limit_dependency(PlanBasedRateLimiter)
    assert dep_ip is not dep_plan

async def test_calls_ip_limiter_with_request_and_response(
    mock_response: MagicMock,
) -> None:
    mock_limiter = AsyncMock()
    mock_request = _make_request_with_container(mock_limiter)
    dep = rate_limit_dependency(IPRateLimiter)

    await dep(request=mock_request, response=mock_response)

    mock_limiter.assert_called_once_with(mock_request, mock_response)

async def test_calls_plan_based_limiter_with_request_and_response(
    mock_response: MagicMock,
) -> None:
    mock_limiter = AsyncMock()
    mock_request = _make_request_with_container(mock_limiter)
    dep = rate_limit_dependency(PlanBasedRateLimiter)

    await dep(request=mock_request, response=mock_response)

    mock_limiter.assert_called_once_with(mock_request, mock_response)

async def test_propagates_limiter_exception(
    mock_response: MagicMock,
) -> None:
    mock_limiter = AsyncMock(side_effect=RuntimeError("rate limit error"))
    mock_request = _make_request_with_container(mock_limiter)
    dep = rate_limit_dependency(IPRateLimiter)

    with pytest.raises(RuntimeError, match="rate limit error"):
        await dep(request=mock_request, response=mock_response)

async def test_returns_none(
    mock_response: MagicMock,
) -> None:
    mock_limiter = AsyncMock(return_value=None)
    mock_request = _make_request_with_container(mock_limiter)
    dep = rate_limit_dependency(IPRateLimiter)

    result = await dep(request=mock_request, response=mock_response)

    assert result is None
