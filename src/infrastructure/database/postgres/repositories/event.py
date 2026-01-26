from datetime import datetime
from typing import Any, cast
from uuid import UUID

from domain.event.models import Event, Properties
from domain.exceptions.app import NotFoundError
from domain.types import ProjectID
from infrastructure.database.postgres.base import PostgresBaseRepository
from infrastructure.serialization.object_to_dict import ObjectDictSerializer


class PostgresEventRepository(PostgresBaseRepository):
    async def add(self, event: Event) -> None:
        await self.execute(
            """
                INSERT INTO event(
                    event_id,
                    project_id,
                    user_id,
                    session_id,
                    event_type,
                    timestamp,
                    properties,
                    created_at
                )
                VALUES($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
                ON CONFLICT
                DO NOTHING
            """,
            event.event_id,
            event.project_id,
            event.user_id,
            event.session_id,
            event.event_type,
            event.timestamp,
            ObjectDictSerializer.to_dict(event.properties),
            event.created_at,
        )

    async def add_many(self, events: list[Event]) -> None:
        await self.executemany(
            """
                INSERT INTO event(
                    event_id,
                    project_id,
                    user_id,
                    session_id,
                    event_type,
                    timestamp,
                    properties,
                    created_at
                )
                VALUES($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
                ON CONFLICT
                DO NOTHING
            """,
            [
                (
                    event.event_id,
                    event.project_id,
                    event.user_id,
                    event.session_id,
                    event.event_type,
                    event.timestamp,
                    ObjectDictSerializer.to_dict(event.properties),
                    event.created_at,
                )
                for event in events
            ],
        )

    async def get_by_project_id(
        self, project_id: ProjectID, limit: int = 100, offset: int = 0
    ) -> list[Event]:
        query = """
            SELECT
                event_id,
                project_id,
                user_id,
                session_id,
                event_type,
                timestamp,
                properties,
                created_at
            FROM event
            WHERE project_id = $1
            LIMIT $2
            OFFSET $3
        """
        rows = await self.fetch_all(query, str(project_id), limit, offset)

        if not rows:
            return []

        return [self._map_row_to_entity(row) for row in rows]

    async def get_by_id(self, event_id: UUID) -> Event:
        query = """
            SELECT
                event_id,
                project_id,
                user_id,
                session_id,
                event_type,
                timestamp,
                properties,
                created_at
            FROM event
            WHERE event_id = $1
        """
        row = await self.fetch_one(query, event_id)

        if not row:
            raise NotFoundError(f"Event by id {event_id} not found")

        return self._map_row_to_entity(row)

    def _map_row_to_entity(self, row: dict[str, Any]) -> Event:
        return Event(
            event_id=cast(UUID, row["event_id"]),
            project_id=cast(UUID, row["project_id"]),
            user_id=cast(str, row["user_id"]),
            session_id=cast(str, row["session_id"]),
            event_type=row["event_type"],
            timestamp=cast(datetime, row["timestamp"]),
            properties=Properties(**row["properties"]),
            created_at=cast(datetime, row["created_at"]),
        )
