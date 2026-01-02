from fastapi import APIRouter, status

router = APIRouter(prefix="/healthz", tags=["Health Check"])


@router.get(
    "",
    summary="Acknowledge service health",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def health_check():
    return {"status": "ok"}
