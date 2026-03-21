from typing import Any, Protocol


DEFAULT_TTL = 300
EVENTS_PER_DAY_TTL = 15 * 60  # 15 min
EVENT_HISTORICAL_TTL = 24 * 60 * 60  # 24 hour
EVENT_FUNNEL_TTL = 45 * 60  # 45 min
EVENT_TOP_PRODUCTS_TTL = 30 * 60  # 30 min
EVENT_RETENTION_TTL = 10 * 60  # 10 min
EVENT_TOP_COUNTRIES_TTL = 10 * 60  # 10 min


class Cache(Protocol):
    async def set(self, key: str, value: Any, ttl: int = 300) -> None: ...  # noqa: ANN401

    async def get(self, key: str) -> Any | None: ...  # noqa: ANN401
