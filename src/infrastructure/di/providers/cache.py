from dishka import Provider, Scope, provide

from domain.cache.repository import Cache
from infrastructure.cache.in_memory import InMemoryCache


class CacheProvider(Provider):
    @provide(scope=Scope.APP)
    def get_cache(self) -> Cache:
        return InMemoryCache()
