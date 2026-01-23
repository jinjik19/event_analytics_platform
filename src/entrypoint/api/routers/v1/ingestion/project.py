from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status

from application.common.error_response import RESPONSE
from application.project.schemas.create_dto import CreateProjectDTO
from application.project.schemas.response_dto import ProjectResponseDTO
from application.project.services.create import CreateProjectService
from infrastructure.rate_limit.dependencies import IPRateLimiter
from infrastructure.rate_limit.fastapi_dependency import rate_limit_dependency
from infrastructure.security.dependencies import token_auth_required


router = APIRouter(
    prefix="/project",
    tags=["Project"],
    route_class=DishkaRoute,
    dependencies=[
        Depends(rate_limit_dependency(IPRateLimiter)),
        Depends(token_auth_required),
    ],
)


@router.post(
    "",
    summary="Create project",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": ProjectResponseDTO},
        status.HTTP_400_BAD_REQUEST: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_403_FORBIDDEN: RESPONSE[status.HTTP_403_FORBIDDEN],
        status.HTTP_422_UNPROCESSABLE_CONTENT: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE[status.HTTP_500_INTERNAL_SERVER_ERROR],
    },
)
async def create_project(
    data: CreateProjectDTO,
    service: FromDishka[CreateProjectService],
) -> ProjectResponseDTO:
    return await service(data)
