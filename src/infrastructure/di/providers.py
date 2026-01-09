from dishka import Provider, Scope, provide

from application.common.uow import IUnitOfWork
from application.project.services.create import CreateProjectService


class ApplicationProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_create_project_service(self, uow: IUnitOfWork) -> CreateProjectService:
        return CreateProjectService(uow)
