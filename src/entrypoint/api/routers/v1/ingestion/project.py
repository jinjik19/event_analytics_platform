from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from application.project.schemas.create_dto import CreateProjectDTO
from application.project.schemas.response_dto import ProjectResponseDTO
from application.project.services.create import CreateProjectService


router = APIRouter(prefix="/project", tags=["Project"], route_class=DishkaRoute)


@router.post(
    "",
    summary="Create project",
    status_code=status.HTTP_200_OK,
    response_model=ProjectResponseDTO,
)
async def create_project(
    data: CreateProjectDTO,
    service: FromDishka[CreateProjectService],
) -> ProjectResponseDTO:
    return await service(data)
