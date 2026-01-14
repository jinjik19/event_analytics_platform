from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from fastapi import Depends, Header

from domain.exceptions.app import UnauthorizedError
from infrastructure.database.postgres.uow import PostgresUnitOfWork


async def get_current_project_id(
    api_key: Annotated[str, Header(alias="X-Api-Key")],
    uow: FromDishka[PostgresUnitOfWork],
) -> UUID:
    project = await uow.project.get_by_api_key(api_key)

    if project:
        return project.project_id

    raise UnauthorizedError("Invalid API key")


CurrentProjectID = Annotated[UUID, Depends(get_current_project_id)]
