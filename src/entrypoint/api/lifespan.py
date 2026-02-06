from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from dishka import AsyncContainer
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from infrastructure.config.settings import settings
from infrastructure.di.providers.types import CacheRedis
from infrastructure.logger.setup import configure_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Lifespan context manager for FastAPI application.

    app: FastAPI
        The FastAPI application instance.
    """
    configure_logger()

    container: AsyncContainer = app.state.dishka_container
    cache_client = await container.get(CacheRedis)

    if settings.is_rate_limit_enabled:
        await FastAPILimiter.init(cache_client)

    yield

    if settings.is_rate_limit_enabled:
        await FastAPILimiter.close()
