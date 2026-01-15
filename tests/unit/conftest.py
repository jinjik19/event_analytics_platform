import pytest
from unittest.mock import AsyncMock, MagicMock
from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from infrastructure.config.settings import AppEnv, Settings

@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)

    uow.project = AsyncMock()
    uow.event = AsyncMock()
    uow.project.add = AsyncMock()

    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None

    return uow

@pytest.fixture
def mock_logger():
    logger = MagicMock(spec=BoundLogger)
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.bind.return_value = logger
    return logger
