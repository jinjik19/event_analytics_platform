from dishka.integrations.fastapi import DishkaRoute, FromDishka, inject
from fastapi import APIRouter, Depends, Request, Response, status

from application.common.error_response import RESPONSE
from application.event.schemas.ingest_dto import IngestEventDTO
from application.event.schemas.response_dto import IngestEventResponseDTO
from application.event.services.ingest import IngestEventService
from domain.types import ProjectID
from infrastructure.rate_limit.dependencies import PlanBasedRateLimiter


@inject
async def rate_limit_check(
    request: Request,
    response: Response,
    limiter: FromDishka[PlanBasedRateLimiter],
) -> None:
    await limiter(request, response)


router = APIRouter(prefix="/event", tags=["Event"], route_class=DishkaRoute)


@router.post(
    "",
    summary="Ingest event",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit_check)],
    responses={
        status.HTTP_200_OK: {"model": IngestEventResponseDTO},
        status.HTTP_400_BAD_REQUEST: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_422_UNPROCESSABLE_CONTENT: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE[status.HTTP_400_BAD_REQUEST],
    },
)
async def ingest_event(
    project_id: FromDishka[ProjectID],
    data: IngestEventDTO,
    service: FromDishka[IngestEventService],
) -> IngestEventResponseDTO:
    event_id = await service(project_id=project_id, data=data)
    return IngestEventResponseDTO(event_id=event_id)
