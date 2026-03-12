from dishka import Provider, Scope, provide
from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from application.event.services.analytics.event_per_day import EventsPerDayService
from application.event.services.analytics.funnel import EventFunnelService
from application.event.services.ingest import IngestEventService
from application.event.services.ingest_batch import IngestEventBatchService
from application.project.services.create import CreateProjectService
from domain.cache.repository import Cache
from domain.event.producer import EventProducer
from domain.event.repository import IEventAnalyticsRepository
from infrastructure.config.settings import Settings


class ApplicationProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_create_project_service(
        self,
        uow: IUnitOfWork,
        logger: BoundLogger,
        settings: Settings,
    ) -> CreateProjectService:
        return CreateProjectService(uow, logger, settings)

    @provide(scope=Scope.REQUEST)
    async def get_ingest_event_service(
        self,
        producer: EventProducer,
        logger: BoundLogger,
        settings: Settings,
    ) -> IngestEventService:
        return IngestEventService(producer, logger, settings)

    @provide(scope=Scope.REQUEST)
    async def get_ingest_event_batch_service(
        self,
        producer: EventProducer,
        logger: BoundLogger,
        settings: Settings,
    ) -> IngestEventBatchService:
        return IngestEventBatchService(producer, logger, settings)

    @provide(scope=Scope.REQUEST)
    async def get_events_per_day(
        self,
        event_dw: IEventAnalyticsRepository,
        logger: BoundLogger,
        cache: Cache,
    ) -> EventsPerDayService:
        return EventsPerDayService(event_dw, logger, cache)

    @provide(scope=Scope.REQUEST)
    async def get_funnel(
        self,
        event_dw: IEventAnalyticsRepository,
        logger: BoundLogger,
        cache: Cache,
    ) -> EventFunnelService:
        return EventFunnelService(event_dw, logger, cache)
