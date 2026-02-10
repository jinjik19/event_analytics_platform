import time

from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from domain.event.consumer import EventConsumer
from infrastructure.config.settings import Settings
from infrastructure.metrics.worker import BATCH_PROCESSING_TIME, EVENTS_PROCESSED, PROCESSING_ERRORS


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

        try:
            start_time = time.time()

            self._logger.info("batch_received", count=len(events))

            domain_events = [consumed.event for consumed in events]
            msg_ids = [e.msg_id for e in events]

            async with self._uow:
                await self._uow.event.add_many(domain_events)
                await self._uow.commit()

            await self._consumer.ack(msg_ids)
            EVENTS_PROCESSED.inc(len(events))

            self._logger.info("batch_processed_and_acked", count=len(msg_ids))
        except Exception as e:
            self._logger.error("batch_processing_failed", error=str(e))
            PROCESSING_ERRORS.labels(error_type="batch_processing_failed").inc()
            raise e
        finally:
            duration = time.time() - start_time
            BATCH_PROCESSING_TIME.observe(duration)

    async def ensure_startup(self) -> None:
        await self._consumer.ensure_group()

    async def update_metrics(self) -> None:
        await self._consumer.update_stream_metrics()
