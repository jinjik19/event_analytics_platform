from datetime import datetime

import pytest
from domain.exceptions.app import InvalidPayloadError
from domain.project.models import Project
from domain.project.types import Plan
from domain.utils.generate_api_key import generate_api_key
from domain.utils.generate_uuid import generate_uuid


async def test_create_project_model():
    project = Project.create(
        name="Test Project",
        plan=Plan.FREE,
        env="test",
    )

    assert project.project_id is not None
    assert project.name == "Test Project"
    assert project.plan == Plan.FREE
    assert project.api_key is not None
    assert project.created_at is not None


async def test_create_project_with_short_name():
    with pytest.raises(InvalidPayloadError):
        Project.create(
            name="a",
            plan=Plan.FREE,
            env="test",
        )


async def test_create_project_with_long_name():
    with pytest.raises(InvalidPayloadError):
        Project.create(
            name="a" * 101,
            plan=Plan.FREE,
            env="test",
        )


async def test_create_project_with_invalid_plan():
    with pytest.raises(InvalidPayloadError):
        Project.create(
            name="Test Project",
            plan="super",
            env="test",
        )


async def test_init_project_model(test_settings):
    project_id = generate_uuid()
    api_key = generate_api_key(test_settings.app_env.value)
    now = datetime.now()

    project = Project(
        project_id=project_id,
        name="Test Project",
        plan=Plan.FREE,
        api_key=api_key,
        created_at=now,
    )

    assert project.project_id == project_id
    assert project.name == "Test Project"
    assert project.plan == Plan.FREE
    assert project.api_key == api_key
    assert project.created_at == now
