from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from domain.event.models import Event
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


class IEventAnalyticsRepository(Protocol):
    async def count_event_by_day(self, project_id: ProjectID) -> list[EventCountByDay]: ...
