from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from domain.event.models import Event, Properties
from domain.event.types import EventType


def dict_to_event(data: dict[str, Any]) -> Event:
    """Convert a dictionary (from msgpack) to an Event instance."""
    properties_data = data.get("properties", {})
    properties = Properties(
        page_url=properties_data.get("page_url"),
        product_id=properties_data.get("product_id"),
        product_name=properties_data.get("product_name"),
        category=properties_data.get("category"),
        price=properties_data.get("price"),
        quantity=properties_data.get("quantity"),
        currency=properties_data.get("currency"),
        country=properties_data.get("country"),
        browser=properties_data.get("browser"),
        os=properties_data.get("os"),
        device_type=properties_data.get("device_type"),
        source=properties_data.get("source"),
        button_clicked=properties_data.get("button_clicked"),
    )

    timestamp = datetime.fromisoformat(data["timestamp"])
    created_at = datetime.fromisoformat(data["created_at"])

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)

    return Event(
        event_id=UUID(data["event_id"]),
        project_id=UUID(data["project_id"]),
        user_id=data.get("user_id"),
        session_id=data.get("session_id"),
        event_type=EventType(data["event_type"]),
        timestamp=timestamp,
        created_at=created_at,
        properties=properties,
    )
