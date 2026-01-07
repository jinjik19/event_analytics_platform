from fastapi import APIRouter, FastAPI

from entrypoint.api.lifespan import lifespan
from entrypoint.api.middleware.logger import StructlogMiddleware
from entrypoint.api.routers import healthz


app = FastAPI(
    title="Event Analytics Platform",
    lifespan=lifespan,
)

app.add_middleware(StructlogMiddleware)

v1 = APIRouter(prefix="/api/v1")

app.include_router(v1)
app.include_router(healthz.router)
