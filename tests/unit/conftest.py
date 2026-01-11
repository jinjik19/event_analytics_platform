import pytest
from unittest.mock import AsyncMock, MagicMock
from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from infrastructure.config.settings import AppEnv, Settings

@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)

    # Настраиваем репозитории внутри UoW
    uow.project = AsyncMock()
    uow.project.add = AsyncMock()

    # Настраиваем контекстный менеджер (async with uow:)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None

    return uow

@pytest.fixture
def mock_logger():
    logger = MagicMock(spec=BoundLogger)
    logger.info = MagicMock()
    logger.error = MagicMock()
    # bind возвращает самого себя (обычное поведение structlog)
    logger.bind.return_value = logger
    return logger

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.app_env = AppEnv.TEST
    return settings
