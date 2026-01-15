import asyncio
from infrastructure.cache.in_memory import InMemoryCache


async def test_in_memory_cache():
    cache = InMemoryCache(max_size=1, ttl=2)
    await cache.set("key", "value")
    assert await cache.get("key") == "value"


async def test_in_memory_cache_max_size():
    cache = InMemoryCache(max_size=1, ttl=2)
    await cache.set("key", "value")
    await cache.set("key2", "value2")
    assert await cache.get("key") is None
    assert await cache.get("key2") == "value2"


async def test_in_memory_cache_ttl():
    cache = InMemoryCache(max_size=1, ttl=2)
    await cache.set("key", "value")
    assert await cache.get("key") == "value"
    await asyncio.sleep(2)
    assert await cache.get("key") is None
