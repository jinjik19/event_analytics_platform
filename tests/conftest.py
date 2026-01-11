import asyncio

import pytest

from infrastructure.config.settings import AppEnv, Settings

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def test_settings() -> Settings:
    from infrastructure.config.settings import settings
    settings.app_env = AppEnv.TEST
    return settings
