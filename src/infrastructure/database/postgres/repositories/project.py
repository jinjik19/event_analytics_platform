from datetime import datetime

from uuid6 import UUID

from domain.project.exceptions import ProjectNotFoundError
from domain.project.models import Project
from domain.project.types import Plan
from infrastructure.database.postgres.base import PostgresBaseRepository


class PostgresProjectRepository(PostgresBaseRepository):
    async def add(self, project: Project) -> None:
        await self.execute(
            """
                INSERT INTO project(project_id, name, api_key, created_at)
                VALUES($1, $2, $3, $4)
            """,
            project.project_id,
            project.name,
            project.api_key,
            project.created_at,
        )

    async def get_by_api_key(self, api_key: str) -> Project | None:
        query = """
            SELECT project_id, name, api_key, created_at
            FROM project
            WHERE api_key = $1
        """
        row = await self.fetch_one(query, api_key)

        if not row:
            raise ProjectNotFoundError(f"Project by api_key {api_key} not Found")

        return self._map_row_to_entity(row)

    async def get_by_id(self, project_id: str) -> Project | None:
        query = """
            SELECT project_id, name, api_key, created_at
            FROM project
            WHERE project_id = $1
        """
        row = await self.fetch_one(query, project_id)

        if not row:
            raise ProjectNotFoundError(f"Project by id {project_id} not found")

        return self._map_row_to_entity(row)

    def _map_row_to_entity(self, row: dict[str, str]) -> Project:
        """
        Приватный метод-маппер.
        Превращает 'грязную' строку БД в чистую Сущность.
        """
        return Project(
            project_id=UUID(row["id"]),
            name=row["name"],
            plan=Plan(row["plan"]),
            api_key=row["api_key"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
