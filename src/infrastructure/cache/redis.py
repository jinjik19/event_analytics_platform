import json
from datetime import datetime
from typing import Any
from uuid import UUID

from infrastructure.di.providers.types import CacheRedis


def json_encoder(obj: Any) -> Any:  # noqa: ANN401
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class RedisCache:
    def __init__(self, redis: CacheRedis) -> None:
        self._redis = redis

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:  # noqa: ANN401
        serialized_value = json.dumps(value, default=json_encoder)
        await self._redis.set(key, serialized_value, ex=ttl)

    async def get(self, key: str) -> Any | None:  # noqa: ANN401
        value = await self._redis.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
