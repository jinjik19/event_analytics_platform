from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from infrastructure.config.settings import settings
from infrastructure.logger.setup import configure_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Lifespan context manager for FastAPI application.

    app: FastAPI
        The FastAPI application instance.
    """
    configure_logger()

    redis_conn = aioredis.from_url(
        url=str(settings.valkey_url),
        encoding="utf-8",
        decode_responses=True,
    )

    if settings.is_rate_limit_enabled:
        await FastAPILimiter.init(redis_conn)

    yield

    if settings.is_rate_limit_enabled and redis_conn:
        await FastAPILimiter.close()

    await redis_conn.close()
