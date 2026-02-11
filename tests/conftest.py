from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from structlog import BoundLogger

from domain.event.models import Event, Properties
from domain.event.types import EventType
from domain.project.models import Project
from domain.project.types import Plan
from domain.utils.generate_api_key import generate_api_key
from domain.utils.generate_uuid import generate_uuid
from infrastructure.config.settings import AppEnv, Settings, settings

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session", autouse=True)
def mock_settings() -> Settings:
    settings.app_env = AppEnv.TEST
    settings.secret_token = "test-secret-token-12345"
    settings.batch_size = 10
    settings.read_timeout_ms = 1000
    settings.metrics_update_interval = 0.1
    return settings


@pytest.fixture
def mock_logger():
    logger = MagicMock(spec=BoundLogger)
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.bind.return_value = logger
    return logger


@pytest.fixture
def make_project():
    def factory(
        project_id: UUID | None = None,
        api_key: str | None = None,
        name: str | None = None,
        env: AppEnv = AppEnv.TEST,
        plan: Plan | None = None,
    ) -> Project:
        return Project(
            project_id=project_id or generate_uuid(),
            api_key=api_key or generate_api_key(env),
            name=name or "Test project",
            plan=plan or Plan.FREE,
            created_at=datetime.now(UTC),
        )

    return factory


@pytest.fixture
def make_event():
    def factory(
        *,
        project_id: UUID | None = None,
        user_id: str | None =None,
        session_id: str | None = None,
        event_type: EventType = EventType.PAGE_VIEW,
        timestamp: datetime | None = None,
        properties: Properties | None = None,
    ) -> Event:
        return Event(
            event_id=generate_uuid(),
            project_id=project_id or generate_uuid(),
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            timestamp=timestamp or datetime.now(tz=UTC),
            properties=properties
            or Properties(
                page_url="https://example.com",
                button_clicked="submit",
                country="NZ",
                browser="Firefox",
                os="Linux"
            ),
            created_at=datetime.now(tz=UTC),
        )

    return factory
