from typing import Any, Protocol


DEFAULT_TTL = 300
EVENTS_PER_DAY_TTL = 15 * 60
EVENT_HISTORICAL_TTL = 24 * 60 * 60
EVENT_FUNNEL_TTL = 45 * 60
EVENT_TOP_PRODUCTS_TTL = 30 * 60


class Cache(Protocol):
    async def set(self, key: str, value: Any, ttl: int = 300) -> None: ...  # noqa: ANN401

    async def get(self, key: str) -> Any | None: ...  # noqa: ANN401
