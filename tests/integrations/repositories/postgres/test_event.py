import pytest
from domain.exceptions.app import NotFoundError
from domain.event.models import Properties
from domain.utils.generate_uuid import generate_uuid


async def test_add_and_get_by_id(event_repository, project_repository, make_event, make_project):
    project = make_project()
    event = make_event(project_id=project.project_id)
    await project_repository.add(project)

    # act
    await event_repository.add(event)
    fetched = await event_repository.get_by_id(event.event_id)

    # assert
    assert fetched.event_id == event.event_id
    assert fetched.project_id == event.project_id
    assert fetched.user_id == event.user_id
    assert fetched.session_id == event.session_id
    assert fetched.event_type == event.event_type
    assert fetched.timestamp == event.timestamp
    assert fetched.created_at == event.created_at
    assert fetched.properties.page_url == event.properties.page_url
    assert fetched.properties.button_clicked == event.properties.button_clicked
    assert fetched.properties.country == event.properties.country
    assert fetched.properties.browser == event.properties.browser
    assert fetched.properties.os == event.properties.os


async def test_get_by_project_id_returns_events(event_repository, project_repository, make_event, make_project):
    project = make_project()
    other_project = make_project(name="other-project")
    await project_repository.add(project)
    await project_repository.add(other_project)
    event_1 = make_event(project_id=project.project_id, event_type="click")
    event_2 = make_event(project_id=project.project_id, event_type="page_view")
    other_event = make_event(project_id=other_project.project_id)

    await event_repository.add(event_1)
    await event_repository.add(event_2)
    await event_repository.add(other_event)

    # act
    events = await event_repository.get_by_project_id(project.project_id)

    # assert
    assert len(events) == 2
    event_ids = {e.event_id for e in events}

    assert event_1.event_id in event_ids
    assert event_2.event_id in event_ids


async def test_get_by_project_id_empty(event_repository):
    events = await event_repository.get_by_project_id(generate_uuid())

    assert events == []


async def test_get_by_id_not_found(event_repository):
    with pytest.raises(NotFoundError) as exc:
        await event_repository.get_by_id(generate_uuid())

    assert "not found" in str(exc.value).lower()


async def test_add_event_with_nullable_fields(event_repository, project_repository, make_event, make_project):
    project = make_project()
    await project_repository.add(project)
    event = make_event(
        project_id=project.project_id,
        user_id=None,
        session_id=None,
        properties=Properties(page_url=None, button_clicked=None),
    )

    await event_repository.add(event)
    fetched = await event_repository.get_by_id(event.event_id)

    assert fetched.project_id == project.project_id
    assert fetched.user_id is None
    assert fetched.session_id is None
    assert fetched.properties.page_url is None
    assert fetched.properties.button_clicked is None
    assert fetched.properties.country is None
    assert fetched.properties.browser is None
    assert fetched.properties.os is None
