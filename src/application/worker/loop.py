import asyncio
import contextlib

from structlog import BoundLogger

from application.worker.batch_processor import BatchProcessor
from application.worker.graceful_killer import GracefulKiller
from infrastructure.config.settings import Settings


class WorkerLoop:
    def __init__(
        self,
        processor: BatchProcessor,
        killer: GracefulKiller,
        logger: BoundLogger,
        settings: Settings,
    ) -> None:
        self._processor = processor
        self._killer = killer
        self._logger = logger
        self._settings = settings
        self._metrics_task: asyncio.Task[None] | None = None

    async def run(self) -> None:
        self._logger.info("worker_started")

        await self._processor.ensure_startup()

        self._metrics_task = asyncio.create_task(self._monitoring_loop())

        try:
            while not self._killer.shutdown_event.is_set():
                try:
                    await self._processor.process()
                except asyncio.CancelledError as e:
                    self._logger.error("worker_task_cancelled", error=str(e))
                    break
                except Exception as e:
                    self._logger.error("worker_unexpected_error", error=str(e))
                    await asyncio.sleep(5)
        finally:
            if self._metrics_task:
                self._metrics_task.cancel()

                with contextlib.suppress(asyncio.CancelledError):
                    await self._metrics_task

        self._logger.info("worker_stopping_gracefully")

    async def _monitoring_loop(self) -> None:
        self._logger.info("metrics_monitor_started")
        while True:
            try:
                await self._processor.update_metrics()
                await asyncio.sleep(self._settings.metrics_update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("metrics_monitor_error", error=str(e))
                await asyncio.sleep(self._settings.metrics_update_interval)
