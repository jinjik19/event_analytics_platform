from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from infrastructure.logger.setup import configure_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager for FastAPI application.

    app: FastAPI
        The FastAPI application instance.
    """
    configure_logger()

    yield
