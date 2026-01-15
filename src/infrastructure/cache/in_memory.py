from typing import Any

from cachetools import TTLCache


class InMemoryCache:
    def __init__(self, max_size: int = 10_000, ttl: int = 300) -> None:
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=max_size, ttl=ttl)

    async def set(self, key: str, value: Any) -> None:  # noqa: ANN401
        self._cache[key] = value

    async def get(self, key: str) -> Any | None:  # noqa: ANN401
        return self._cache.get(key)
