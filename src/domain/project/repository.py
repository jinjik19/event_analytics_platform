from typing import Protocol

from domain.project.models import Project


class IProjectRepository(Protocol):
    def add(self, project: Project) -> None: ...

    def get_by_api_key(self, api_key: str) -> Project | None: ...

    def get_by_id(self, project_id: str) -> Project | None: ...
