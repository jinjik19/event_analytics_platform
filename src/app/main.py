from app.api.routers import healthz

import uvicorn
from fastapi import APIRouter, FastAPI


app = FastAPI(
    title="Event Analytics Platform",
)

v1 = APIRouter(prefix="/api/v1")
app.include_router(v1)

app.include_router(healthz.router)


if __name__ == "__main__":
    uvicorn.run("__main__:app", host="0.0.0.0", port=8000, reload=True)
