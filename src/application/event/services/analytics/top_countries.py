from datetime import date

from structlog import BoundLogger

from application.event.schemas.top_countries import (
    EventTopCountriesQueryParams,
    EventTopCountriesResponseDTO,
)
from domain.cache.repository import EVENT_HISTORICAL_TTL, EVENT_TOP_COUNTRIES_TTL, Cache
from domain.event.repository import EventTopCountriesParams, IEventAnalyticsRepository
from domain.types import ProjectID


class EventTopCountriesService:
    def __init__(
        self, event_dw: IEventAnalyticsRepository, logger: BoundLogger, cache: Cache
    ) -> None:
        self._logger = logger
        self._event_dw = event_dw
        self._cache = cache

    async def __call__(
        self, project_id: ProjectID, params: EventTopCountriesQueryParams
    ) -> list[EventTopCountriesResponseDTO]:
        self._logger.info("Get top countries for project", project_id=project_id)
        cache_key = (
            f"analytics:top_countries:{project_id}"
            f":{params.sort_by}"
            f":{params.date_from}:{params.date_to}"
            f":{params.limit}"
        )

        cached_data = await self._cache.get(cache_key)

        ttl = EVENT_HISTORICAL_TTL if params.date_to < date.today() else EVENT_TOP_COUNTRIES_TTL

        if cached_data is not None:
            return [EventTopCountriesResponseDTO(**item) for item in cached_data]

        data = await self._event_dw.top_countries(
            params=EventTopCountriesParams(
                project_id=project_id,
                date_from=params.date_from,
                date_to=params.date_to,
                limit=params.limit,
                sort_by=params.sort_by,
            )
        )
        result = [
            EventTopCountriesResponseDTO(
                country=item.country,
                unique_users=item.unique_users,
                events_count=item.events_count,
                revenue=item.revenue,
            )
            for item in data
        ]

        await self._cache.set(cache_key, [r.model_dump(mode="json") for r in result], ttl=ttl)

        return result
