from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator, model_validator

from domain.event.models import Properties
from domain.event.types import EventType


class PropertiesDTO(BaseModel):
    page_url: HttpUrl | None = None
    # Product context
    product_id: str | None = Field(None, min_length=1, max_length=100)
    product_name: str | None = Field(None, max_length=500)
    category: str | None = Field(None, max_length=200)
    price: float | None = Field(None, gt=0, le=1_000_000)
    quantity: int | None = Field(None, ge=1, le=10_000)
    currency: str | None = Field(None, pattern=r"^[A-Z]{3}$")
    # User context
    country: str | None = Field(None, pattern=r"^[A-Z]{2}$")
    browser: str | None = Field(None, max_length=100)
    os: str | None = Field(None, max_length=100)
    device_type: str | None = Field(None, pattern=r"^(mobile|desktop|tablet)$")
    # Marketing
    source: str | None = Field(None, max_length=100)
    # Interaction
    button_clicked: str | None = Field(None, max_length=100)

    def to_domain(self) -> Properties:
        domain_price = round(self.price * 100) if self.price is not None else None

        return Properties(
            page_url=str(self.page_url) if self.page_url else None,
            product_id=self.product_id,
            product_name=self.product_name,
            category=self.category,
            price=domain_price,
            quantity=self.quantity,
            currency=self.currency,
            country=self.country,
            browser=self.browser,
            os=self.os,
            device_type=self.device_type,
            source=self.source,
            button_clicked=self.button_clicked,
        )


class IngestEventDTO(BaseModel):
    user_id: str | None = None
    session_id: str | None = None
    event_type: EventType
    timestamp: datetime
    properties: PropertiesDTO

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)

        now = datetime.now(UTC)

        if v > now + timedelta(minutes=5):
            raise ValueError("timestamp cannot be in the future")

        if v < now - timedelta(days=30):
            raise ValueError("timestamp is too old (max 30 days)")

        return v

    @model_validator(mode="after")
    def validate_event_consistency(self) -> "IngestEventDTO":
        props = self.properties

        match self.event_type:
            case EventType.PURCHASE:
                if not props.product_id:
                    raise ValueError("PURCHASE requires product_id")
                if props.price is None:
                    raise ValueError("PURCHASE requires price")
                if props.quantity is None:
                    raise ValueError("PURCHASE requires quantity")
            case EventType.ADD_TO_CART | EventType.REMOVE_FROM_CART:
                if not props.product_id:
                    raise ValueError(f"{self.event_type} requires product_id")
            case EventType.PRODUCT_VIEW:
                if not props.product_id:
                    raise ValueError("PRODUCT_VIEW requires product_id")

        return self


class IngestEventBatchDTO(BaseModel):
    events: list[IngestEventDTO] = Field(..., min_length=1, max_length=500)

    @field_validator("events", mode="before")
    @classmethod
    def filter_valid_events(cls, raw_events: Any) -> Any:  # noqa: ANN401
        if not isinstance(raw_events, list):
            return raw_events

        valid_events = []
        for item in raw_events:
            try:
                IngestEventDTO.model_validate(item)
                valid_events.append(item)
            except ValidationError:
                continue

        return valid_events
