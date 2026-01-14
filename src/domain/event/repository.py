from typing import Protocol
from uuid import UUID

from domain.event.models import Event


class IEventRepository(Protocol):
    async def add(self, event: Event) -> None: ...
    async def get_by_project_id(self, project_id: UUID) -> list[Event]: ...
    async def get_by_id(self, event_id: UUID) -> Event: ...
