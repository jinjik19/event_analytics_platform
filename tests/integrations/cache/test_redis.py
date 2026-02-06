import asyncio
import pytest


async def test_redis_cache_set_get_basic(fake_redis_cache):
    await fake_redis_cache.set("key", "value", ttl=2)
    result = await fake_redis_cache.get("key")
    assert result == "value"


async def test_redis_cache_json_serialization(fake_redis_cache):
    data = {"name": "Test", "count": 123, "is_active": True}

    await fake_redis_cache.set("complex_key", data, ttl=2)
    result = await fake_redis_cache.get("complex_key")

    assert result == data
    assert result["count"] == 123


async def test_redis_cache_ttl(fake_redis_cache):
    await fake_redis_cache.set("key_ttl", "value", ttl=1)

    assert await fake_redis_cache.get("key_ttl") == "value"

    await asyncio.sleep(1.1)

    assert await fake_redis_cache.get("key_ttl") is None


async def test_redis_cache_get_missing(fake_redis_cache):
    result = await fake_redis_cache.get("non_existent_key")
    assert result is None
