import asyncio

from structlog import BoundLogger

from application.worker.batch_processor import BatchProcessor
from application.worker.graceful_killer import GracefulKiller


class WorkerLoop:
    def __init__(
        self,
        processor: BatchProcessor,
        killer: GracefulKiller,
        logger: BoundLogger,
    ) -> None:
        self._processor = processor
        self._killer = killer
        self._logger = logger

    async def run(self) -> None:
        self._logger.info("worker_started")

        await self._processor.ensure_startup()

        while not self._killer.shutdown_event.is_set():
            try:
                await self._processor.process()
            except asyncio.CancelledError as e:
                self._logger.error("worker_task_cancelled", error=str(e))
                break
            except Exception as e:
                self._logger.error("worker_unexpected_error", error=str(e))
                await asyncio.sleep(5)

        self._logger.info("worker_stopping_gracefully")
