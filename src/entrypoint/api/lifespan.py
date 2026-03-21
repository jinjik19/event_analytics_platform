import asyncio
import contextlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from clickhouse_connect.driver import AsyncClient
from dishka import AsyncContainer
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from structlog import BoundLogger

from infrastructure.config.settings import settings
from infrastructure.database.clickhouse.base import ClickhouseBaseRepository
from infrastructure.di.providers.types import CacheRedis
from infrastructure.logger.setup import configure_logger
from infrastructure.metrics.cdc import CdcLagMonitor


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Lifespan context manager for FastAPI application.

    app: FastAPI
        The FastAPI application instance.
    """
    configure_logger()

    container: AsyncContainer = app.state.dishka_container
    cache_client = await container.get(CacheRedis)
    ch_client = await container.get(AsyncClient)
    logger = await container.get(BoundLogger)

    if settings.is_rate_limit_enabled:
        await FastAPILimiter.init(cache_client)

    async with httpx.AsyncClient() as http_client:
        monitor = CdcLagMonitor(
            dwh_repo=ClickhouseBaseRepository(ch_client),
            http_client=http_client,
            logger=logger,
            settings=settings,
        )
        task = asyncio.create_task(monitor.run())
        yield
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    if settings.is_rate_limit_enabled:
        await FastAPILimiter.close()
