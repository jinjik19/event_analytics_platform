from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from infrastructure.config.settings import settings
from infrastructure.logger.setup import configure_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager for FastAPI application.

    app: FastAPI
        The FastAPI application instance.
    """
    configure_logger()

    logger = structlog.get_logger()
    logger.info("Starting application", app_name=settings.app_name, level=settings.log_level)

    yield

    logger.info("Shutting down application", app_name=settings.app_name)
