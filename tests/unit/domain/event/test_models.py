
from datetime import datetime
import pytest
from domain.event.models import Event, Properties, UserProperties, Device
from domain.utils.generate_uuid import generate_uuid


async def test_create_properties_model():
    properties = Properties(
        page_url="http://test.com/page1",
        button_clicked="button1",
    )

    assert properties.page_url == "http://test.com/page1"
    assert properties.button_clicked == "button1"


async def test_create_user_properties_model():
    user_properties = UserProperties(
        country="NZ",
    )

    assert user_properties.country == "NZ"


async def test_create_device_model():
    device = Device(
        os="Linux",
        browser="Firefox",
    )

    assert device.os == "Linux"
    assert device.browser == "Firefox"


async def test_create_event_model():
    project_id = generate_uuid()
    user_id = generate_uuid()
    session_id = generate_uuid()
    now = datetime.now()


    event = Event.create(
        project_id=project_id,
        user_id=user_id,
        session_id=session_id,
        event_type="page_view",
        timestamp=now,
        properties=Properties(
            page_url="http://test.com/page1",
            button_clicked=None,
        ),
        user_properties=UserProperties(
            country="NZ",
        ),
        device=Device(
            os=None,
            browser="Firefox",
        ),
    )

    assert event.event_id is not None
    assert event.project_id == project_id
    assert event.user_id == user_id
    assert event.session_id == session_id
    assert event.event_type == "page_view"
    assert event.timestamp == now
    assert event.properties.page_url == "http://test.com/page1"
    assert event.properties.button_clicked is None
    assert event.user_properties.country == "NZ"
    assert event.device.os is None
    assert event.device.browser == "Firefox"
    assert event.created_at is not None


async def test_init_event_model():
    event_id = generate_uuid()
    project_id = generate_uuid()
    user_id = generate_uuid()
    session_id = generate_uuid()
    now = datetime.now()


    event = Event(
        event_id=event_id,
        project_id=project_id,
        user_id=user_id,
        session_id=session_id,
        event_type="page_view",
        timestamp=now,
        properties=Properties(
            page_url="http://test.com/page1",
            button_clicked=None,
        ),
        user_properties=UserProperties(
            country="NZ",
        ),
        device=Device(
            os=None,
            browser="Firefox",
        ),
        created_at=now,
    )

    assert event.event_id is not None
    assert event.project_id == project_id
    assert event.user_id == user_id
    assert event.session_id == session_id
    assert event.event_type == "page_view"
    assert event.timestamp == now
    assert event.properties.page_url == "http://test.com/page1"
    assert event.properties.button_clicked is None
    assert event.user_properties.country == "NZ"
    assert event.device.os is None
    assert event.device.browser == "Firefox"
    assert event.created_at == now
