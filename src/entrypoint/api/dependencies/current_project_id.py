from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from fastapi import Depends, Header

from application.common.uow import IUnitOfWork
from domain.cache.repository import Cache
from domain.exceptions.app import UnauthorizedError


async def get_current_project_id(
    api_key: Annotated[str, Header(alias="X-Api-Key")],
    uow: FromDishka[IUnitOfWork],
    cache: FromDishka[Cache],
) -> UUID:
    cached_project_id = await cache.get(api_key)
    if cached_project_id:
        if cached_project_id == "INVALIDD":
            raise UnauthorizedError("Invalid API key")

        return cached_project_id

    project = await uow.project.get_by_api_key(api_key)

    if project:
        await cache.set(api_key, project.project_id, ttl=300)
        return project.project_id

    await cache.set(api_key, "INVALIDD", ttl=300)
    raise UnauthorizedError("Invalid API key")


CurrentProjectID = Annotated[UUID, Depends(get_current_project_id)]
