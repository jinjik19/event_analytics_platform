from datetime import datetime
from typing import cast

from domain.exceptions.app import NotFoundError
from domain.project.models import Project
from domain.project.types import Plan
from domain.types import ProjectID
from infrastructure.database.postgres.base import PostgresBaseRepository


class PostgresProjectRepository(PostgresBaseRepository):
    async def add(self, project: Project) -> None:
        await self.execute(
            """
                INSERT INTO project(project_id, name, plan, api_key, created_at)
                VALUES($1, $2, $3, $4, $5)
            """,
            project.project_id,
            project.name,
            project.plan.value,
            project.api_key,
            project.created_at,
        )

    async def get_by_api_key(self, api_key: str) -> Project:
        query = """
            SELECT project_id, name, plan, api_key, created_at
            FROM project
            WHERE api_key = $1
        """
        row = await self.fetch_one(query, api_key)

        if not row:
            raise NotFoundError(f"Project by api_key {api_key} not Found")

        return self._map_row_to_entity(row)

    async def get_by_id(self, project_id: ProjectID) -> Project:
        query = """
            SELECT project_id, name, plan, api_key, created_at
            FROM project
            WHERE project_id = $1
        """
        row = await self.fetch_one(query, project_id)

        if not row:
            raise NotFoundError(f"Project by id {project_id} not found")

        return self._map_row_to_entity(row)

    def _map_row_to_entity(self, row: dict[str, str]) -> Project:
        return Project(
            project_id=cast(ProjectID, row["project_id"]),
            name=row["name"],
            plan=Plan(row["plan"]),
            api_key=row["api_key"],
            created_at=cast(datetime, row["created_at"]),
        )
