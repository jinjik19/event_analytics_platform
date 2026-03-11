from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status

from application.common.error_response import RESPONSE
from application.event.schemas.events_per_day import EventsPerDayResponseDTO
from application.event.services.analytics.event_per_day import EventsPerDayService
from domain.types import ProjectID
from infrastructure.rate_limit.dependencies import PlanBasedRateLimiter
from infrastructure.rate_limit.fastapi_dependency import rate_limit_dependency


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    route_class=DishkaRoute,
    dependencies=[Depends(rate_limit_dependency(PlanBasedRateLimiter))],
)


@router.get(
    "/events-per-day",
    summary="Events per day",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": list[EventsPerDayResponseDTO]},
        status.HTTP_400_BAD_REQUEST: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_401_UNAUTHORIZED: RESPONSE[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_422_UNPROCESSABLE_CONTENT: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE[status.HTTP_500_INTERNAL_SERVER_ERROR],
    },
)
async def events_per_day(
    project_id: FromDishka[ProjectID],
    service: FromDishka[EventsPerDayService],
) -> list[EventsPerDayResponseDTO]:
    return await service(project_id=project_id)
