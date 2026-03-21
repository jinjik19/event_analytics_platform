from datetime import date

from structlog import BoundLogger

from application.event.schemas.funnel import EventFunnelQueryParams, EventFunnelResponseDTO
from domain.cache.repository import EVENT_FUNNEL_TTL, EVENT_HISTORICAL_TTL, Cache
from domain.event.repository import EventFunnelParams, IEventAnalyticsRepository
from domain.types import ProjectID


class EventFunnelService:
    def __init__(
        self, event_dw: IEventAnalyticsRepository, logger: BoundLogger, cache: Cache
    ) -> None:
        self._logger = logger
        self._event_dw = event_dw
        self._cache = cache

    async def __call__(
        self, project_id: ProjectID, params: EventFunnelQueryParams
    ) -> list[EventFunnelResponseDTO]:
        self._logger.info("Get event funnel for project", project_id=project_id)
        cache_key = (
            f"analytics:funnel:{project_id}"
            f":{':'.join(params.steps)}"
            f":{params.date_from}:{params.date_to}"
            f":{params.window_days}"
        )

        cached_data = await self._cache.get(cache_key)

        ttl = EVENT_HISTORICAL_TTL if params.date_to < date.today() else EVENT_FUNNEL_TTL

        if cached_data is not None:
            return [EventFunnelResponseDTO(**item) for item in cached_data]

        data = await self._event_dw.funnel(
            params=EventFunnelParams(
                project_id=project_id,
                steps=params.steps,
                date_from=params.date_from,
                date_to=params.date_to,
                window_days=params.window_days,
            )
        )
        result = [
            EventFunnelResponseDTO(
                step=item.step,
                users=item.users,
                conversion_from_prev=item.conversion_from_prev,
                conversion_from_top=item.conversion_from_top,
            )
            for item in data
        ]

        await self._cache.set(cache_key, [r.model_dump(mode="json") for r in result], ttl=ttl)

        return result
