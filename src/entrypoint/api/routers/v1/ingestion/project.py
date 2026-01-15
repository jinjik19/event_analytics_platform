from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from application.common.error_response import RESPONSE
from application.project.schemas.create_dto import CreateProjectDTO
from application.project.schemas.response_dto import ProjectResponseDTO
from application.project.services.create import CreateProjectService


router = APIRouter(prefix="/project", tags=["Project"], route_class=DishkaRoute)


@router.post(
    "",
    summary="Create project",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": ProjectResponseDTO},
        status.HTTP_400_BAD_REQUEST: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_422_UNPROCESSABLE_CONTENT: RESPONSE[status.HTTP_400_BAD_REQUEST],
        status.HTTP_500_INTERNAL_SERVER_ERROR: RESPONSE[status.HTTP_400_BAD_REQUEST],
    },
)
async def create_project(
    data: CreateProjectDTO,
    service: FromDishka[CreateProjectService],
) -> ProjectResponseDTO:
    return await service(data)
