import pytest

from domain.project.types import Plan
from infrastructure.config.settings import Settings
from infrastructure.rate_limit.config import get_plan_rate_limit


@pytest.fixture
def mock_settings() -> Settings:
    settings = Settings(
        rate_limit_free_rpm=100,
        rate_limit_pro_rpm=1000,
        rate_limit_enterprise_rpm=10000,
        rate_limit_no_auth_rpm=10,
    )
    return settings


def test_get_plan_rate_limit_free(mock_settings: Settings) -> None:
    result = get_plan_rate_limit(Plan.FREE, mock_settings)
    assert result == 100


def test_get_plan_rate_limit_pro(mock_settings: Settings) -> None:
    result = get_plan_rate_limit(Plan.PRO, mock_settings)
    assert result == 1000


def test_get_plan_rate_limit_enterprise(mock_settings: Settings) -> None:
    result = get_plan_rate_limit(Plan.ENTERPRISE, mock_settings)
    assert result == 10000
