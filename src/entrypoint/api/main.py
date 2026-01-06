from fastapi import APIRouter, FastAPI

from entrypoint.api.routers import healthz


app = FastAPI(
    title="Event Analytics Platform",
)

v1 = APIRouter(prefix="/api/v1")
app.include_router(v1)

app.include_router(healthz.router)
