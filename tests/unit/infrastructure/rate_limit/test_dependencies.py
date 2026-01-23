from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domain.project.types import Plan
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
        mock_validator: MagicMock,
        mock_request: MagicMock,
        mock_response: MagicMock,
    ) -> None:
        limiter = IPRateLimiter(
            settings=mock_settings_disabled, token_validator=mock_validator
        )

        await limiter(mock_request, mock_response)

    async def test_ip_limiter_uses_client_ip(
        self,
        mock_settings: Settings,
        mock_validator: MagicMock,
        mock_request: MagicMock,
        mock_response: MagicMock,
    ) -> None:
        mock_settings.is_rate_limit_enabled = False
        mock_request.client.host = "10.0.0.1"

        limiter = IPRateLimiter(
            settings=mock_settings, token_validator=mock_validator
        )

        await limiter(mock_request, mock_response)

    async def test_ip_limiter_handles_no_client(
        self,
        mock_settings: Settings,
        mock_validator: MagicMock,
        mock_request: MagicMock,
        mock_response: MagicMock,
    ) -> None:
        mock_settings.is_rate_limit_enabled = False
        mock_request.client = None

        limiter = IPRateLimiter(
            settings=mock_settings, token_validator=mock_validator
        )

        await limiter(mock_request, mock_response)

    async def test_authorized_request_skips_rate_limit(
        self,
        mock_settings: Settings,
        mock_validator: MagicMock,
        mock_request: MagicMock,
        mock_response: MagicMock,
    ) -> None:
        mock_validator.validate.return_value = True
        mock_request.headers = {"Authorization": "Bearer valid-token"}

        limiter = IPRateLimiter(
            settings=mock_settings, token_validator=mock_validator
        )

        await limiter(mock_request, mock_response)

        mock_validator.validate.assert_called_once_with("valid-token")

    def test_is_authorized_valid_token(
        self,
        mock_settings: Settings,
        mock_validator: MagicMock,
        mock_request: MagicMock,
    ) -> None:
        mock_validator.validate.return_value = True
        mock_request.headers = {"Authorization": "Bearer valid-token"}

        limiter = IPRateLimiter(
            settings=mock_settings, token_validator=mock_validator
        )

        assert limiter._is_authorized(mock_request) is True

    def test_is_authorized_invalid_token(
        self,
        mock_settings: Settings,
        mock_validator: MagicMock,
        mock_request: MagicMock,
    ) -> None:
        mock_validator.validate.return_value = False
        mock_request.headers = {"Authorization": "Bearer wrong-token"}

        limiter = IPRateLimiter(
            settings=mock_settings, token_validator=mock_validator
        )

        assert limiter._is_authorized(mock_request) is False

    def test_is_authorized_no_header(
        self,
        mock_settings: Settings,
        mock_validator: MagicMock,
        mock_request: MagicMock,
    ) -> None:
        mock_request.headers = {}

        limiter = IPRateLimiter(
            settings=mock_settings, token_validator=mock_validator
        )

        assert limiter._is_authorized(mock_request) is False
        mock_validator.validate.assert_not_called()

    def test_is_authorized_no_bearer_prefix(
        self,
        mock_settings: Settings,
        mock_validator: MagicMock,
        mock_request: MagicMock,
    ) -> None:
        mock_request.headers = {"Authorization": "Token something"}

        limiter = IPRateLimiter(
            settings=mock_settings, token_validator=mock_validator
        )

        assert limiter._is_authorized(mock_request) is False
        mock_validator.validate.assert_not_called()
