from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import APIRouter, FastAPI

from entrypoint.api.lifespan import lifespan
from entrypoint.api.middleware.logger import StructlogMiddleware
from entrypoint.api.routers import healthz, project
from infrastructure.database.postgres.providers import DbProvider
from infrastructure.di.providers.application import ApplicationProvider
from infrastructure.di.providers.logger import LoggerProvider
from infrastructure.di.providers.settings import SettingsProvider


def create_app() -> FastAPI:
    app = FastAPI(
        title="Event Analytics Platform",
        lifespan=lifespan,
    )

    app.add_middleware(StructlogMiddleware)

    v1 = APIRouter(prefix="/api/v1")
    v1.include_router(project.router)

    app.include_router(v1)
    app.include_router(healthz.router)

    container = make_async_container(
        DbProvider(),
        ApplicationProvider(),
        SettingsProvider(),
        LoggerProvider(),
    )
    setup_dishka(container, app)

    return app


app = create_app()
