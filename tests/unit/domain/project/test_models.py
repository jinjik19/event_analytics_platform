
import pytest
from domain.project.exceptions import InvalidProjectNameError, InvalidProjectPlanError
from domain.project.models import Project
from domain.project.types import Plan


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
    with pytest.raises(InvalidProjectNameError):
        project = Project.create(
            name="a",
            plan=Plan.FREE,
            env="test",
        )


async def test_create_project_with_long_name():
    with pytest.raises(InvalidProjectNameError):
        project = Project.create(
            name="a" * 101,
            plan=Plan.FREE,
            env="test",
        )


async def test_create_project_with_invalid_plan():
    with pytest.raises(InvalidProjectPlanError):
        project = Project.create(
            name="Test Project",
            plan="super",
            env="test",
        )
