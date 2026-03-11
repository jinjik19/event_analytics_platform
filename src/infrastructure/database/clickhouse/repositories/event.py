from domain.event.repository import EventCountByDay
from domain.types import ProjectID
from infrastructure.database.clickhouse.base import ClickhouseBaseRepository


class EventAnalyticsRepository(ClickhouseBaseRepository):
    async def count_event_by_day(self, project_id: ProjectID) -> list[EventCountByDay]:
        result = await self.query(
            """
            SELECT
                toDate(timestamp) AS event_date,
                COUNT(event_id) AS total
            FROM analytics.event
            WHERE project_id = {project_id:UUID}
            GROUP BY event_date
            ORDER BY event_date
            """,
            parameters={"project_id": project_id},
        )

        return [EventCountByDay(date=row[0], count=row[1]) for row in result.result_rows]
