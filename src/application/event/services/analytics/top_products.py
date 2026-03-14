from datetime import date
from uuid import UUID

from structlog import BoundLogger

from application.event.schemas.top_products import (
    EventTopProductsQueryParams,
    EventTopProductsResponseDTO,
)
from domain.cache.repository import EVENT_HISTORICAL_TTL, EVENT_TOP_PRODUCTS_TTL, Cache
from domain.event.repository import EventTopProductsParams, IEventAnalyticsRepository


class EventTopProductsService:
    def __init__(
        self, event_dw: IEventAnalyticsRepository, logger: BoundLogger, cache: Cache
    ) -> None:
        self._logger = logger
        self._event_dw = event_dw
        self._cache = cache

    async def __call__(
        self, project_id: UUID, params: EventTopProductsQueryParams
    ) -> list[EventTopProductsResponseDTO]:
        self._logger.info("Get top products for project", project_id=project_id)
        cache_key = (
            f"analytics:top_products:{project_id}"
            f":{params.metric}"
            f":{params.date_from}:{params.date_to}"
            f":{params.limit}"
        )

        cached_data = await self._cache.get(cache_key)

        ttl = EVENT_HISTORICAL_TTL if params.date_to < date.today() else EVENT_TOP_PRODUCTS_TTL

        if cached_data is not None:
            return [EventTopProductsResponseDTO(**item) for item in cached_data]

        data = await self._event_dw.top_products(
            params=EventTopProductsParams(
                project_id=project_id,
                metric=params.metric,
                date_from=params.date_from,
                date_to=params.date_to,
                limit=params.limit,
            )
        )
        result = [
            EventTopProductsResponseDTO(
                category=item.category,
                product_id=item.product_id,
                product_name=item.product_name,
                add_to_cart_count=item.add_to_cart_count,
                purchase_count=item.purchase_count,
                revenue=item.revenue,
            )
            for item in data
        ]

        await self._cache.set(cache_key, [r.model_dump(mode="json") for r in result], ttl=ttl)

        return result
