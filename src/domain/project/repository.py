from typing import Protocol

from domain.project.models import Project
from domain.types import ProjectID


class IProjectRepository(Protocol):
    async def add(self, project: Project) -> None: ...
    async def get_by_api_key(self, api_key: str) -> Project: ...
    async def get_by_id(self, project_id: ProjectID) -> Project: ...
