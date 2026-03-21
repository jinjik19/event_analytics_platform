from structlog import BoundLogger

from application.event.schemas.events_per_day import EventsPerDayResponseDTO
from domain.cache.repository import EVENTS_PER_DAY_TTL, Cache
from domain.event.repository import IEventAnalyticsRepository
from domain.types import ProjectID


class EventsPerDayService:
    def __init__(
        self, event_dw: IEventAnalyticsRepository, logger: BoundLogger, cache: Cache
    ) -> None:
        self._logger = logger
        self._event_dw = event_dw
        self._cache = cache

    async def __call__(self, project_id: ProjectID) -> list[EventsPerDayResponseDTO]:
        self._logger.info("Get events per day for project", project_id=project_id)
        cache_key = f"analytics:events_per_day:{project_id}"

        cached_data = await self._cache.get(cache_key)

        if cached_data is not None:
            return [EventsPerDayResponseDTO(**item) for item in cached_data]

        data = await self._event_dw.count_event_by_day(project_id)
        result = [EventsPerDayResponseDTO(date=item.date, count=item.count) for item in data]

        await self._cache.set(
            cache_key, [r.model_dump(mode="json") for r in result], ttl=EVENTS_PER_DAY_TTL
        )

        return result
