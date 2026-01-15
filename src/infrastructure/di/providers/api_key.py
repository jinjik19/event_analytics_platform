from dishka import Provider, Scope, provide
from fastapi import Request

from application.common.uow import IUnitOfWork
from domain.cache.repository import Cache
from domain.exceptions.app import UnauthorizedError
from domain.types import ProjectID
from infrastructure.config.settings import Settings


class ApiKeyProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_project_id(
        self,
        request: Request,
        uow: IUnitOfWork,
        cache: Cache,
        settings: Settings,
    ) -> ProjectID:
        api_key = request.headers.get("X-Api-Key")
        if not api_key:
            raise UnauthorizedError("Missing API Key")

        if not api_key.startswith(f"wk_{settings.app_env}"):
            raise UnauthorizedError("Bad API Key")

        if cached_project_id := await cache.get(api_key):
            return ProjectID(cached_project_id)

        if project := await uow.project.get_by_api_key(api_key):
            await cache.set(api_key, project.project_id)
            return project.project_id

        raise UnauthorizedError("Invalid API Key")
