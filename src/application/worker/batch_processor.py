from structlog import BoundLogger

from domain.event.consumer import EventConsumer
from infrastructure.config.settings import Settings


class BatchProcessor:
    def __init__(self, consumer: EventConsumer, logger: BoundLogger, settings: Settings) -> None:
        self._consumer = consumer
        self._logger = logger
        self._batch_size = settings.batch_size
        self._timeout_ms = settings.read_timeout_ms

    async def process(self) -> None:
        events = await self._consumer.read_batch(
            count=self._batch_size,
            block_ms=self._timeout_ms,
        )

        if not events:
            return

        self._logger.info("batch_received", count=len(events))

        # TODO: add logic for prcoess

        msg_ids = [e.msg_id for e in events]
        await self._consumer.ack(msg_ids)

        self._logger.info("batch_processed_and_acked", count=len(msg_ids))

    async def ensure_startup(self) -> None:
        await self._consumer.ensure_group()
