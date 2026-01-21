from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.project.models import Project
from domain.project.types import Plan
from domain.utils.generate_uuid import generate_uuid
from infrastructure.config.settings import AppEnv, Settings
from infrastructure.rate_limit.dependencies import IPRateLimiter, PlanBasedRateLimiter


@pytest.fixture
def mock_settings() -> Settings:
    settings = MagicMock(spec=Settings)
    settings.is_rate_limit_enabled = True
    settings.rate_limit_enabled = True
    settings.app_env = AppEnv.TEST
    settings.rate_limit_free_rpm = 100
    settings.rate_limit_pro_rpm = 1000
    settings.rate_limit_enterprise_rpm = 10000
    settings.rate_limit_no_auth_rpm = 10
    settings.rate_limit_project_create_rpm = 5
    return settings


@pytest.fixture
def mock_settings_disabled() -> Settings:
    settings = MagicMock(spec=Settings)
    settings.is_rate_limit_enabled = False
    return settings


@pytest.fixture
def mock_uow() -> AsyncMock:
    uow = AsyncMock()
    uow.project = AsyncMock()
    uow.project.get_by_api_key = AsyncMock(return_value=None)
    uow.project.get_by_id = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def mock_cache() -> AsyncMock:
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_request() -> MagicMock:
    request = MagicMock()
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def mock_response() -> MagicMock:
    return MagicMock()

class TestPlanBasedRateLimiter:
    async def test_rate_limit_disabled_returns_early(
        self,
        mock_settings_disabled: Settings,
        mock_uow: AsyncMock,
        mock_cache: AsyncMock,
        mock_request: MagicMock,
        mock_response: MagicMock,
    ) -> None:
        limiter = PlanBasedRateLimiter(
            settings=mock_settings_disabled, uow=mock_uow, cache=mock_cache
        )

        await limiter(mock_request, mock_response)

        # Should return early without checking headers
        mock_uow.project.get_by_api_key.assert_not_called()
        mock_cache.get.assert_not_called()

    async def test_no_api_key_returns_ip_identifier(
        self,
        mock_settings: Settings,
        mock_uow: AsyncMock,
        mock_cache: AsyncMock,
        mock_request: MagicMock,
    ) -> None:
        mock_request.headers = {}
        limiter = PlanBasedRateLimiter(
            settings=mock_settings, uow=mock_uow, cache=mock_cache
        )

        identifier, rpm = await limiter._get_identifier_and_rpm(None, mock_request)

        assert identifier == "ip:127.0.0.1"
        assert rpm == 10

    async def test_invalid_api_key_prefix_returns_ip_identifier(
        self,
        mock_settings: Settings,
        mock_uow: AsyncMock,
        mock_cache: AsyncMock,
        mock_request: MagicMock,
    ) -> None:
        limiter = PlanBasedRateLimiter(
            settings=mock_settings, uow=mock_uow, cache=mock_cache
        )

        identifier, rpm = await limiter._get_identifier_and_rpm(
            "invalid_key", mock_request
        )

        assert identifier == "ip:127.0.0.1"
        assert rpm == 10

    async def test_valid_api_key_from_cache(
        self,
        mock_settings: Settings,
        mock_uow: AsyncMock,
        mock_cache: AsyncMock,
        mock_request: MagicMock,
        make_project,
    ) -> None:
        project = make_project(plan=Plan.PRO)
        mock_cache.get.return_value = str(project.project_id)
        mock_uow.project.get_by_id.return_value = project

        limiter = PlanBasedRateLimiter(
            settings=mock_settings, uow=mock_uow, cache=mock_cache
        )

        identifier, rpm = await limiter._get_identifier_and_rpm(
            project.api_key, mock_request
        )

        assert identifier == f"project:{project.project_id}"
        assert rpm == 1000  # PRO plan
        mock_cache.get.assert_called_once_with(f"api_key:{project.api_key}")
        mock_uow.project.get_by_id.assert_called_once()

    async def test_valid_api_key_from_database(
        self,
        mock_settings: Settings,
        mock_uow: AsyncMock,
        mock_cache: AsyncMock,
        mock_request: MagicMock,
        make_project,
    ) -> None:
        project = make_project(plan=Plan.ENTERPRISE)
        mock_cache.get.return_value = None
        mock_uow.project.get_by_api_key.return_value = project

        limiter = PlanBasedRateLimiter(
            settings=mock_settings, uow=mock_uow, cache=mock_cache
        )

        identifier, rpm = await limiter._get_identifier_and_rpm(
            project.api_key, mock_request
        )

        assert identifier == f"project:{project.project_id}"
        assert rpm == 10000  # ENTERPRISE plan
        mock_uow.project.get_by_api_key.assert_called_once_with(project.api_key)
        mock_cache.set.assert_called_once_with(project.api_key, project.project_id)

    async def test_api_key_not_found_returns_ip_identifier(
        self,
        mock_settings: Settings,
        mock_uow: AsyncMock,
        mock_cache: AsyncMock,
        mock_request: MagicMock,
    ) -> None:
        mock_cache.get.return_value = None
        mock_uow.project.get_by_api_key.return_value = None

        limiter = PlanBasedRateLimiter(
            settings=mock_settings, uow=mock_uow, cache=mock_cache
        )

        identifier, rpm = await limiter._get_identifier_and_rpm(
            "wk_test_nonexistent", mock_request
        )

        assert identifier == "ip:127.0.0.1"
        assert rpm == 10

    def test_get_ip_identifier_with_client(
        self,
        mock_settings: Settings,
        mock_uow: AsyncMock,
        mock_cache: AsyncMock,
        mock_request: MagicMock,
    ) -> None:
        mock_request.client.host = "192.168.1.1"
        limiter = PlanBasedRateLimiter(
            settings=mock_settings, uow=mock_uow, cache=mock_cache
        )

        result = limiter._get_ip_identifier(mock_request)

        assert result == "ip:192.168.1.1"

    def test_get_ip_identifier_without_client(
        self,
        mock_settings: Settings,
        mock_uow: AsyncMock,
        mock_cache: AsyncMock,
        mock_request: MagicMock,
    ) -> None:
        mock_request.client = None
        limiter = PlanBasedRateLimiter(
            settings=mock_settings, uow=mock_uow, cache=mock_cache
        )

        result = limiter._get_ip_identifier(mock_request)

        assert result == "ip:unknown"


class TestIPRateLimiter:
    async def test_rate_limit_disabled_returns_early(
        self,
        mock_settings_disabled: Settings,
        mock_request: MagicMock,
        mock_response: MagicMock,
    ) -> None:
        limiter = IPRateLimiter(settings=mock_settings_disabled)

        # Should not raise any exception
        await limiter(mock_request, mock_response)

    async def test_ip_limiter_uses_client_ip(
        self,
        mock_settings: Settings,
        mock_request: MagicMock,
        mock_response: MagicMock,
    ) -> None:
        mock_settings.is_rate_limit_enabled = False
        mock_request.client.host = "10.0.0.1"

        limiter = IPRateLimiter(settings=mock_settings)

        # Should complete without error when rate limiting is disabled
        await limiter(mock_request, mock_response)

    async def test_ip_limiter_handles_no_client(
        self,
        mock_settings: Settings,
        mock_request: MagicMock,
        mock_response: MagicMock,
    ) -> None:
        mock_settings.is_rate_limit_enabled = False
        mock_request.client = None

        limiter = IPRateLimiter(settings=mock_settings)

        # Should complete without error when rate limiting is disabled
        await limiter(mock_request, mock_response)
