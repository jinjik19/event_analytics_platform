from dishka import Provider, Scope, provide
from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from application.events.services.ingest import IngestEventService
from application.project.services.create import CreateProjectService
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
        logger: BoundLogger,
        settings: Settings,
    ) -> IngestEventService:
        return IngestEventService(logger, settings)
