import pytest
from domain.exceptions.app import NotFoundError
from domain.utils.generate_uuid import generate_uuid


async def test_add_and_get_by_id(project_repository, make_project, test_settings):
    project = make_project(env=test_settings.app_env)

    # act
    await project_repository.add(project)
    fetched = await project_repository.get_by_id(project.project_id)

    # assert
    assert fetched.project_id == project.project_id
    assert fetched.name == project.name
    assert fetched.plan == project.plan
    assert fetched.api_key == project.api_key
    assert fetched.created_at == project.created_at


async def test_add_and_get_by_api_key(project_repository, make_project):
    project = make_project(api_key="unique-api-key")

    await project_repository.add(project)
    fetched = await project_repository.get_by_api_key("unique-api-key")

    assert fetched.project_id == project.project_id
    assert fetched.api_key == "unique-api-key"
    assert fetched.plan == project.plan


async def test_get_by_id_not_found(project_repository):
    with pytest.raises(NotFoundError) as exc:
        await project_repository.get_by_id(generate_uuid())

    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_get_by_api_key_not_found(project_repository):
    with pytest.raises(NotFoundError) as exc:
        await project_repository.get_by_api_key("missing-api-key")

    assert "not found" in str(exc.value).lower()
