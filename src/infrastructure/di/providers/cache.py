from dishka import Provider, Scope, provide

from infrastructure.cache.in_memory import InMemoryCache


class CacheProvider(Provider):
    @provide(scope=Scope.APP)
    def get_cache(self) -> InMemoryCache:
        return InMemoryCache()
