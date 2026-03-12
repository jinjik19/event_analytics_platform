from datetime import date, timedelta

from pydantic import BaseModel, Field

from domain.event.types import EventType


class EventFunnelQueryParams(BaseModel):
    steps: list[EventType] = [
        EventType.PAGE_VIEW,
        EventType.PRODUCT_VIEW,
        EventType.ADD_TO_CART,
        EventType.PURCHASE,
    ]
    date_from: date = Field(default_factory=lambda: date.today() - timedelta(days=30))
    date_to: date = Field(default_factory=date.today)
    window_days: int = 7


class EventFunnelResponseDTO(BaseModel):
    step: EventType
    users: int
    conversion_from_prev: float | None
    conversion_from_top: float | None
