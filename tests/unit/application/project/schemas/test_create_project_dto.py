
from pydantic import ValidationError
import pytest
from application.project.schemas.create_dto import CreateProjectDTO
from domain.project.types import Plan


async def test_create_project_dto_valid():
    dto = CreateProjectDTO(**{
        "name": "test_project",
        "plan": Plan.FREE
    })

    assert dto.name == "test_project"
    assert dto.plan == Plan.FREE


async def test_create_project_dto_short_name():
    with pytest.raises(ValidationError) as exc:
        dto = CreateProjectDTO(**{
            "name": "te",
            "plan": Plan.FREE
        })

    errors = exc.value.errors()

    assert len(errors) == 1
    assert errors[0]["loc"] == ("name",)
    assert errors[0]["type"] == "string_too_short"


async def test_create_project_dto_long_name():
    with pytest.raises(ValidationError) as exc:
        dto = CreateProjectDTO(**{
            "name": "t" * 101,
            "plan": Plan.FREE
        })

    errors = exc.value.errors()

    assert len(errors) == 1
    assert errors[0]["loc"] == ("name",)
    assert errors[0]["type"] == "string_too_long"


async def test_create_project_dto_invalid_plan():
    with pytest.raises(ValidationError) as exc:
        dto = CreateProjectDTO(**{
            "name": "test_project",
            "plan": "super",
        })

    errors = exc.value.errors()

    assert len(errors) == 1
    assert errors[0]["loc"] == ("plan",)
    assert errors[0]["type"] == "enum"
