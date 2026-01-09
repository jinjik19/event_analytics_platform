import logging

from application.common.uow import IUnitOfWork
from application.project.schemas.create_dto import CreateProjectDTO
from application.project.schemas.response_dto import ProjectResponseDTO
from domain.project.models import Project
from infrastructure.config.settings import Settings


class CreateProjectService:
    def __init__(self, uow: IUnitOfWork, logger: logging.Logger, settings: Settings) -> None:
        self._uow = uow
        self._logger = logger
        self._settings = settings

    async def __call__(self, data: CreateProjectDTO) -> ProjectResponseDTO:
        self._logger.info("Creating project", project_name=data.name)
        new_project = Project.create(
            name=data.name, plan=data.plan, env=str(self._settings.app_env)
        )

        async with self._uow:
            await self._uow.project.add(new_project)
            await self._uow.commit()

        self._logger.info("Project created", project_id=str(new_project.project_id))
        return ProjectResponseDTO(
            project_id=str(new_project.project_id),
            name=new_project.name,
            api_key=new_project.api_key,
            plan=new_project.plan,
            created_at=new_project.created_at,
        )
