import pytest
from dishka import make_async_container, Provider, Scope, provide
from unittest.mock import MagicMock, AsyncMock

from application.worker.batch_processor import BatchProcessor
from application.worker.graceful_killer import GracefulKiller
from application.worker.loop import WorkerLoop
from infrastructure.di.providers.worker import WorkerProvider
from domain.event.consumer import EventConsumer
from infrastructure.config.settings import Settings
from structlog import BoundLogger


class MockDependenciesProvider(Provider):
    scope = Scope.APP

    @provide
    def get_settings(self) -> Settings:
        return Settings(batch_size=5, read_timeout_ms=100)

    @provide
    def get_logger(self) -> BoundLogger:
        return MagicMock(spec=BoundLogger)

    @provide
    def get_consumer(self) -> EventConsumer:
        return AsyncMock(spec=EventConsumer)


@pytest.mark.asyncio
async def test_worker_container_assembly():
    container = make_async_container(
        WorkerProvider(),
        MockDependenciesProvider()
    )

    try:
        async with container() as scope:
            killer = await scope.get(GracefulKiller)
            assert isinstance(killer, GracefulKiller)

            processor = await scope.get(BatchProcessor)
            assert isinstance(processor, BatchProcessor)
            assert processor._batch_size == 5

            loop = await scope.get(WorkerLoop)
            assert isinstance(loop, WorkerLoop)
            assert loop._processor is processor
            assert loop._killer is killer

    finally:
        await container.close()
