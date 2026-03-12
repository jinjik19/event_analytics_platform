from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from domain.event.models import Event
from domain.event.types import EventType
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


class IEventAnalyticsRepository(Protocol):
    async def count_event_by_day(self, project_id: ProjectID) -> list[EventCountByDay]: ...

    async def funnel(self, params: EventFunnelParams) -> list[EventFunnelResul]: ...
