from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from domain.event.types import EventType
from domain.utils.generate_uuid import generate_uuid


@dataclass(frozen=True, slots=True)
class Properties:
    page_url: str | None = None
    # Product context
    product_id: str | None = None
    product_name: str | None = None
    category: str | None = None
    price: int | None = None
    quantity: int | None = None
    currency: str | None = None
    # User context
    country: str | None = None
    browser: str | None = None
    os: str | None = None
    device_type: str | None = None
    # Marketing
    source: str | None = None
    # Interaction
    button_clicked: str | None = None


@dataclass(frozen=True, slots=True)
class Event:
    event_id: UUID
    project_id: UUID
    user_id: str | None
    session_id: str | None
    event_type: EventType
    timestamp: datetime
    properties: Properties
    created_at: datetime

    @classmethod
    def create(
        cls,
        project_id: UUID,
        user_id: str | None,
        session_id: str | None,
        event_type: EventType,
        timestamp: datetime,
        properties: Properties,
    ) -> "Event":
        return cls(
            event_id=generate_uuid(),
            project_id=project_id,
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            timestamp=timestamp,
            properties=properties,
            created_at=datetime.now(UTC),
        )
