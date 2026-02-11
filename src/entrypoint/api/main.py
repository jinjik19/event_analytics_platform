from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from entrypoint.api.lifespan import lifespan
from entrypoint.api.middleware.exception_handler import ExceptionHandlerMiddleware
from entrypoint.api.middleware.logger import StructlogMiddleware
from entrypoint.api.routers import health
from entrypoint.api.routers.v1.ingestion import event, project
from infrastructure.config.settings import AppEnv, settings
from infrastructure.di.providers.api_key import ApiKeyProvider
from infrastructure.di.providers.application import ApplicationProvider
from infrastructure.di.providers.cache import CacheProvider
from infrastructure.di.providers.db import DbProvider
from infrastructure.di.providers.logger import LoggerProvider
from infrastructure.di.providers.rate_limit import RateLimitProvider
from infrastructure.di.providers.security import SecurityProvider
from infrastructure.di.providers.settings import SettingsProvider
from infrastructure.di.providers.stream import StreamProvider


async def re_raise_exception(request: Request, exc: Exception) -> Response:
    raise exc


def create_app() -> FastAPI:
    app = FastAPI(
        title="Event Analytics Platform",
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/docs/openapi.json",
        exception_handlers={},
    )

    app.add_middleware(ExceptionHandlerMiddleware)

    if settings.app_env != AppEnv.TEST:
        app.add_middleware(StructlogMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=[
                "Authorization",
                "X-Api-Key",
            ],
        )

    app.add_exception_handler(RequestValidationError, re_raise_exception)
    app.add_exception_handler(StarletteHTTPException, re_raise_exception)

    container = make_async_container(
        DbProvider(),
        ApplicationProvider(),
        SettingsProvider(),
        LoggerProvider(),
        CacheProvider(),
        ApiKeyProvider(),
        RateLimitProvider(),
        SecurityProvider(),
        FastapiProvider(),
        StreamProvider(),
    )
    setup_dishka(container, app)
    Instrumentator().instrument(app).expose(app)

    v1 = APIRouter(prefix="/api/v1")
    v1.include_router(project.router)
    v1.include_router(event.router)

    app.include_router(v1)
    app.include_router(health.router)

    return app


app = create_app()
