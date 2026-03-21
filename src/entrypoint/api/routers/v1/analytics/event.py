from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Query, status

from application.common.error_response import RESPONSE
from application.event.schemas.events_per_day import EventsPerDayResponseDTO
from application.event.schemas.funnel import EventFunnelQueryParams, EventFunnelResponseDTO
from application.event.schemas.retention import EventRetentionQueryParams, EventRetentionResponseDTO
from application.event.schemas.top_countries import (
    EventTopCountriesQueryParams,
    EventTopCountriesResponseDTO,
)
from application.event.schemas.top_products import (
    EventTopProductsQueryParams,
    EventTopProductsResponseDTO,
)
from application.event.services.analytics.event_per_day import EventsPerDayService
from application.event.services.analytics.funnel import EventFunnelService
from application.event.services.analytics.retention import EventRetentionService
from application.event.services.analytics.top_countries import EventTopCountriesService
from application.event.services.analytics.top_products import EventTopProductsService
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


@router.get(
    "/funnel",
    summary="Funnel",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": list[EventFunnelResponseDTO]},
        status.HTTP_400_BAD_REQUEST: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_401_UNAUTHORIZED: RESPONSE[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_422_UNPROCESSABLE_CONTENT: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE[status.HTTP_500_INTERNAL_SERVER_ERROR],
    },
)
async def funnel(
    project_id: FromDishka[ProjectID],
    query_params: Annotated[EventFunnelQueryParams, Query()],
    service: FromDishka[EventFunnelService],
) -> list[EventFunnelResponseDTO]:
    return await service(project_id=project_id, params=query_params)


@router.get(
    "/top-products",
    summary="Top Products",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": list[EventTopProductsResponseDTO]},
        status.HTTP_400_BAD_REQUEST: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_401_UNAUTHORIZED: RESPONSE[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_422_UNPROCESSABLE_CONTENT: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE[status.HTTP_500_INTERNAL_SERVER_ERROR],
    },
)
async def top_products(
    project_id: FromDishka[ProjectID],
    query_params: Annotated[EventTopProductsQueryParams, Query()],
    service: FromDishka[EventTopProductsService],
) -> list[EventTopProductsResponseDTO]:
    return await service(project_id=project_id, params=query_params)


@router.get(
    "/retention",
    summary="Retention",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": list[EventRetentionResponseDTO]},
        status.HTTP_400_BAD_REQUEST: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_401_UNAUTHORIZED: RESPONSE[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_422_UNPROCESSABLE_CONTENT: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE[status.HTTP_500_INTERNAL_SERVER_ERROR],
    },
)
async def retention(
    project_id: FromDishka[ProjectID],
    query_params: Annotated[EventRetentionQueryParams, Query()],
    service: FromDishka[EventRetentionService],
) -> list[EventRetentionResponseDTO]:
    return await service(project_id=project_id, params=query_params)


@router.get(
    "/top-countries",
    summary="Top Countries",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": list[EventTopCountriesResponseDTO]},
        status.HTTP_400_BAD_REQUEST: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_401_UNAUTHORIZED: RESPONSE[status.HTTP_401_UNAUTHORIZED],
        status.HTTP_422_UNPROCESSABLE_CONTENT: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE[status.HTTP_500_INTERNAL_SERVER_ERROR],
    },
)
async def top_countries(
    project_id: FromDishka[ProjectID],
    query_params: Annotated[EventTopCountriesQueryParams, Query()],
    service: FromDishka[EventTopCountriesService],
) -> list[EventTopCountriesResponseDTO]:
    return await service(project_id=project_id, params=query_params)
