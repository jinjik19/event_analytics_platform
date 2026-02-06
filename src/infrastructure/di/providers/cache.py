from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from redis.asyncio import from_url

from domain.cache.repository import Cache
from infrastructure.cache.redis import RedisCache
from infrastructure.config.settings import Settings
from infrastructure.di.providers.types import CacheRedis


class CacheProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_client(self, settings: Settings) -> AsyncIterable[CacheRedis]:
        client = from_url(
            url=settings.cache_url,
            encoding="utf-8",
            decode_responses=True,
        )
        yield CacheRedis(client)
        await client.aclose()  # type: ignore[attr-defined]

    @provide
    def get_cache(self, client: CacheRedis) -> Cache:
        return RedisCache(client)
