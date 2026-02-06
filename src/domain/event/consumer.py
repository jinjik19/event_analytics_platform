from dataclasses import dataclass
from typing import Protocol

from domain.event.models import Event


@dataclass(frozen=True, slots=True)
class ConsumedEvent:
    msg_id: str
    event: Event


class EventConsumer(Protocol):
    async def ensure_group(self) -> None:
        """Create the consumer group if it doesn't exist."""
        ...

    async def read_batch(self, batch_size: int = 100) -> list[ConsumedEvent]:
        """Read a batch of events from the stream."""
        ...

    async def ack(self, msg_ids: list[str]) -> None:
        """Acknowledge the processing of events by their message IDs."""
        ...
