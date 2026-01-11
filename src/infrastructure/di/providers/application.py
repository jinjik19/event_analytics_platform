from dishka import Provider, Scope, provide
from structlog import BoundLogger

from application.common.uow import IUnitOfWork
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
