from datetime import datetime
from uuid import UUID

from domain.utils.generate_uuid import generate_uuid


class Properties:
    __slots__ = ("_button_clicked", "_page_url")

    def __init__(
        self,
        page_url: str | None,
        button_clicked: str | None,
    ) -> None:
        self._page_url = page_url
        self._button_clicked = button_clicked

    # --- GETTERS ---

    @property
    def page_url(self) -> str | None:
        return self._page_url

    @property
    def button_clicked(self) -> str | None:
        return self._button_clicked


class UserProperties:
    __slots__ = "_country"

    def __init__(self, country: str | None) -> None:
        self._country = country

    # --- GETTERS ---

    @property
    def country(self) -> str | None:
        return self._country


class Device:
    __slots__ = ("_browser", "_os")

    def __init__(self, browser: str | None, os: str | None) -> None:
        self._browser = browser
        self._os = os

    # --- GETTERS ---

    @property
    def browser(self) -> str:
        return self._browser

    @property
    def os(self) -> str:
        return self._os


class Event:
    __slots__ = (
        "_created_at",
        "_device",
        "_event_id",
        "_event_type",
        "_project_id",
        "_properties",
        "_session_id",
        "_timestamp",
        "_user_id",
        "_user_properties",
    )

    def __init__(
        self,
        event_id: UUID,
        project_id: UUID,
        user_id: UUID | None,
        session_id: UUID | None,
        event_type: str,
        timestamp: datetime,
        properties: Properties,
        user_properties: UserProperties,
        device: Device,
        created_at: datetime,
    ) -> None:
        self._event_id = event_id
        self._project_id = project_id
        self._user_id = user_id
        self._session_id = session_id
        self._event_type = event_type
        self._timestamp = timestamp
        self._properties = properties
        self._user_properties = user_properties
        self._device = device
        self._created_at = created_at

    # --- FACTORY ---

    @classmethod
    def create(
        cls,
        project_id: UUID,
        user_id: UUID | None,
        session_id: UUID | None,
        event_type: str,
        timestamp: datetime,
        properties: dict[str, str],
        user_properties: dict[str, str],
        device: dict[str, str],
    ) -> str:
        now = datetime.now()
        new_id = generate_uuid()

        return cls(
            event_id=new_id,
            project_id=project_id,
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            timestamp=timestamp,
            properties=Properties(
                page_url=properties.get("page_url"),
                button_clicked=properties.get("button_clicked"),
            ),
            user_properties=UserProperties(country=user_properties.get("country")),
            device=Device(browser=device.get("browser"), os=device.get("os")),
            created_at=now,
        )

    # --- GETTERS ---

    @property
    def event_id(self) -> UUID:
        return self._event_id

    @property
    def project_id(self) -> UUID:
        return self._project_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def session_id(self) -> UUID:
        return self._session_id

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def properties(self) -> dict[str, str]:
        return self._properties

    @property
    def user_properties(self) -> dict[str, str]:
        return self._user_properties

    @property
    def device(self) -> dict[str, str]:
        return self._device

    @property
    def created_at(self) -> datetime:
        return self._created_at
