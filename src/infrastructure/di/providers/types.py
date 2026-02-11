from typing import TYPE_CHECKING, Any, NewType

from redis.asyncio import Redis


if TYPE_CHECKING:
    RedisClient = Redis[Any]
else:
    RedisClient = Redis


CacheRedis = NewType("CacheRedis", RedisClient)
StreamRedis = NewType("StreamRedis", RedisClient)
