from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from domain.event.models import Event
from domain.event.types import AnalyticsMetrics, EventType
from domain.types import ProjectID


class IEventRepository(Protocol):
    async def add(self, event: Event) -> None: ...
    async def add_many(self, events: list[Event]) -> None: ...
    async def get_by_project_id(
        self, project_id: ProjectID, limit: int, offset: int
    ) -> list[Event]: ...
    async def get_by_id(self, event_id: UUID) -> Event: ...


@dataclass(frozen=True, slots=True)
class EventCountByDay:
    date: date
    count: int


@dataclass(slots=True)
class EventFunnelParams:
    project_id: ProjectID
    steps: list[EventType]
    date_from: date
    date_to: date
    window_days: int


@dataclass(frozen=True, slots=True)
class EventFunnelResul:
    step: EventType
    users: int
    conversion_from_prev: float | None
    conversion_from_top: float | None


@dataclass(slots=True)
class EventTopProductsParams:
    project_id: ProjectID
    metric: AnalyticsMetrics
    date_from: date
    date_to: date
    limit: int


@dataclass(frozen=True, slots=True)
class EventTopProductsResul:
    category: str
    product_id: str
    product_name: str
    add_to_cart_count: int
    purchase_count: int
    revenue: float


@dataclass(slots=True)
class EventRetentionParams:
    project_id: ProjectID
    date_from: date
    date_to: date
    days: int


@dataclass(frozen=True, slots=True)
class EventRetentionResul:
    cohort_date: date
    day_number: int
    retained_users: int
    cohort_size: int
    retention_pct: float


class IEventAnalyticsRepository(Protocol):
    async def count_event_by_day(self, project_id: ProjectID) -> list[EventCountByDay]: ...

    async def funnel(self, params: EventFunnelParams) -> list[EventFunnelResul]: ...

    async def top_products(self, params: EventTopProductsParams) -> list[EventTopProductsResul]: ...

    async def retention(self, params: EventRetentionParams) -> list[EventRetentionResul]: ...
