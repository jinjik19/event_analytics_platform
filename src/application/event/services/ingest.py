from uuid import UUID

from structlog import BoundLogger

from application.common.uow import IUnitOfWork
from application.event.schemas.ingest_dto import IngestEventDTO
from domain.event.models import Event, Properties
from infrastructure.config.settings import Settings


class IngestEventService:
    def __init__(self, uow: IUnitOfWork, logger: BoundLogger, settings: Settings) -> None:
        self._uow = uow
        self._logger = logger
        self._settings = settings

    async def __call__(self, project_id: UUID, data: IngestEventDTO) -> UUID:
        self._logger.info("Ingesting event", event_type=data.event_type, project_id=project_id)
        new_event = Event.create(
            project_id=project_id,
            user_id=data.user_id,
            session_id=data.session_id,
            event_type=data.event_type,
            timestamp=data.timestamp,
            properties=Properties(**data.properties.model_dump()),
        )

        async with self._uow:
            await self._uow.event.add(new_event)
            await self._uow.commit()

        self._logger.info("Event ingested", event_id=str(new_event.event_id))
        return new_event.event_id
