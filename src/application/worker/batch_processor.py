from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from domain.event.consumer import EventConsumer
from infrastructure.config.settings import Settings


class BatchProcessor:
    def __init__(
        self, consumer: EventConsumer, uow: IUnitOfWork, logger: BoundLogger, settings: Settings
    ) -> None:
        self._consumer = consumer
        self._uow = uow
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

        domain_events = [consumed.event for consumed in events]
        msg_ids = [e.msg_id for e in events]

        try:
            async with self._uow:
                await self._uow.event.add_many(domain_events)
                await self._uow.commit()

            await self._consumer.ack(msg_ids)
        except Exception as e:
            self._logger.error("batch_processing_failed", error=str(e))
            raise e

        self._logger.info("batch_processed_and_acked", count=len(msg_ids))

    async def ensure_startup(self) -> None:
        await self._consumer.ensure_group()
