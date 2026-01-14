from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from application.events.schemas.ingest_dto import IngestEventDTO
from application.events.schemas.response_dto import IngestEventResponseDTO
from application.events.services.ingest import IngestEventService
from entrypoint.api.dependencies.current_project_id import CurrentProjectID


router = APIRouter(prefix="/event", tags=["Event"], route_class=DishkaRoute)


@router.post(
    "",
    summary="Ingest event",
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_event(
    project_id: CurrentProjectID,
    data: IngestEventDTO,
    service: FromDishka[IngestEventService],
) -> IngestEventResponseDTO:
    event_id = await service(project_id=project_id, data=data)
    return IngestEventResponseDTO(event_id=event_id)
