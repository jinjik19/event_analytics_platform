from dishka import Provider, Scope, provide
from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from application.worker.batch_processor import BatchProcessor
from application.worker.graceful_killer import GracefulKiller
from application.worker.loop import WorkerLoop
from domain.event.consumer import EventConsumer
from infrastructure.config.settings import Settings


class WorkerProvider(Provider):
    scope = Scope.APP

    @provide
    def get_killer(self) -> GracefulKiller:
        return GracefulKiller()

    @provide(scope=Scope.REQUEST)
    def get_processor(
        self,
        consumer: EventConsumer,
        uow: IUnitOfWork,
        logger: BoundLogger,
        settings: Settings,
    ) -> BatchProcessor:
        return BatchProcessor(consumer, uow, logger, settings)

    @provide(scope=Scope.REQUEST)
    def get_loop(
        self,
        processor: BatchProcessor,
        killer: GracefulKiller,
        logger: BoundLogger,
        settings: Settings,
    ) -> WorkerLoop:
        return WorkerLoop(processor, killer, logger, settings)
