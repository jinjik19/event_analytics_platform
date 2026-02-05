import pytest
from unittest.mock import AsyncMock, MagicMock
from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from infrastructure.config.settings import AppEnv, Settings
from infrastructure.security.token_validators.secret_token_validator import SecretTokenValidator

@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)

    uow.project = AsyncMock()
    uow.event = AsyncMock()
    uow.project.add = AsyncMock()
    uow.project.get_by_api_key = AsyncMock(return_value=None)
    uow.project.get_by_id = AsyncMock(return_value=None)

    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None

    return uow


@pytest.fixture
def mock_producer():
    producer = AsyncMock()
    producer.publish = AsyncMock()
    producer.publish_batch = AsyncMock()
    return producer


@pytest.fixture
def mock_logger():
    logger = MagicMock(spec=BoundLogger)
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.bind.return_value = logger
    return logger


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


@pytest.fixture
def mock_cache() -> AsyncMock:
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_validator() -> MagicMock:
    validator = MagicMock(spec=SecretTokenValidator)
    validator.validate = MagicMock(return_value=True)
    return validator
