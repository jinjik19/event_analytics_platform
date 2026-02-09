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

    async def read_batch(self, count: int = 100, block_ms: int = 1000) -> list[ConsumedEvent]:
        """Read a batch of events from the stream."""
        ...

    async def ack(self, msg_ids: list[str]) -> None:
        """Acknowledge the processing of events by their message IDs."""
        ...
