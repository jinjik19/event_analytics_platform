from typing import Protocol

from domain.event.models import Event


class EventProducer(Protocol):
    async def publish(self, event: Event) -> None: ...

    async def publish_batch(self, events: list[Event]) -> None: ...
