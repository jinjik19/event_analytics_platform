from datetime import UTC, datetime
from uuid import UUID

import pytest

from domain.event.models import Device, Event, Properties, UserProperties
from domain.project.models import Project
from domain.project.types import Plan
from domain.utils.generate_api_key import generate_api_key
from domain.utils.generate_uuid import generate_uuid
from infrastructure.config.settings import AppEnv, Settings, settings

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session", autouse=True)
def test_settings() -> Settings:
    settings.app_env = AppEnv.TEST
    return settings


@pytest.fixture
def make_project():
    def factory(
        project_id: UUID | None = None,
        api_key: str | None = None,
        name: str | None = None,
        env: AppEnv = AppEnv.TEST,
    ) -> Project:
        return Project(
            project_id=project_id or generate_uuid(),
            api_key=api_key or generate_api_key(env),
            name=name or "Test project",
            plan=Plan.FREE,
            created_at=datetime.now(UTC),
        )

    return factory


@pytest.fixture
def make_event():
    def factory(
        *,
        project_id=None,
        user_id=None,
        session_id=None,
        event_type="page_view",
        timestamp=None,
        properties=None,
        user_properties=None,
        device=None,
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
            ),
            user_properties=user_properties or UserProperties(country="DE"),
            device=device or Device(browser="Firefox", os="Linux"),
            created_at=datetime.now(tz=UTC),
        )

    return factory
