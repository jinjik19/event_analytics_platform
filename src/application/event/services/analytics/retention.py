from datetime import date

from structlog import BoundLogger

from application.event.schemas.retention import (
    EventRetentionQueryParams,
    EventRetentionResponseDTO,
)
from domain.cache.repository import EVENT_HISTORICAL_TTL, EVENT_RETENTION_TTL, Cache
from domain.event.repository import EventRetentionParams, IEventAnalyticsRepository
from domain.types import ProjectID


class EventRetentionService:
    def __init__(
        self, event_dw: IEventAnalyticsRepository, logger: BoundLogger, cache: Cache
    ) -> None:
        self._logger = logger
        self._event_dw = event_dw
        self._cache = cache

    async def __call__(
        self, project_id: ProjectID, params: EventRetentionQueryParams
    ) -> list[EventRetentionResponseDTO]:
        self._logger.info("Get retention for project", project_id=project_id)
        cache_key = (
            f"analytics:retention:{project_id}:{params.date_from}:{params.date_to}:{params.days}"
        )

        cached_data = await self._cache.get(cache_key)

        ttl = EVENT_HISTORICAL_TTL if params.date_to < date.today() else EVENT_RETENTION_TTL

        if cached_data is not None:
            return [EventRetentionResponseDTO(**item) for item in cached_data]

        data = await self._event_dw.retention(
            params=EventRetentionParams(
                project_id=project_id,
                date_from=params.date_from,
                date_to=params.date_to,
                days=params.days,
            )
        )
        result = [
            EventRetentionResponseDTO(
                cohort_date=item.cohort_date,
                day_number=item.day_number,
                retained_users=item.retained_users,
                cohort_size=item.cohort_size,
                retention_pct=item.retention_pct,
            )
            for item in data
        ]

        await self._cache.set(cache_key, [r.model_dump(mode="json") for r in result], ttl=ttl)

        return result
