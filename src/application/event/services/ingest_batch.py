from uuid import UUID

from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from application.event.schemas.ingest_dto import IngestEventBatchDTO
from application.event.schemas.response_dto import IngestEventBatchResponseDTO
from domain.event.models import Event
from infrastructure.config.settings import Settings


class IngestEventBatchService:
    def __init__(self, uow: IUnitOfWork, logger: BoundLogger, settings: Settings) -> None:
        self._uow = uow
        self._logger = logger
        self._settings = settings

    async def __call__(
        self, project_id: UUID, data: IngestEventBatchDTO
    ) -> IngestEventBatchResponseDTO:
        self._logger.info("Ingesting event batch", events=len(data.events), project_id=project_id)
        new_events = [
            Event.create(
                project_id=project_id,
                user_id=dto.user_id,
                session_id=dto.session_id,
                event_type=dto.event_type,
                timestamp=dto.timestamp,
                properties=dto.properties.to_domain(),
            )
            for dto in data.events
        ]

        async with self._uow:
            await self._uow.event.add_many(new_events)
            await self._uow.commit()

        self._logger.info("Events ingested", events=len(new_events))
        return IngestEventBatchResponseDTO(event_ids=[event.event_id for event in new_events])
