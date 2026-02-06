from uuid import UUID

from structlog import BoundLogger

from application.event.schemas.ingest_dto import IngestEventDTO
from application.event.schemas.response_dto import IngestEventResponseDTO
from domain.event.models import Event
from domain.event.producer import EventProducer
from infrastructure.config.settings import Settings


class IngestEventService:
    def __init__(self, producer: EventProducer, logger: BoundLogger, settings: Settings) -> None:
        self._producer = producer
        self._logger = logger
        self._settings = settings

    async def __call__(self, project_id: UUID, data: IngestEventDTO) -> IngestEventResponseDTO:
        new_event = Event.create(
            project_id=project_id,
            user_id=data.user_id,
            session_id=data.session_id,
            event_type=data.event_type,
            timestamp=data.timestamp,
            properties=data.properties.to_domain(),
        )

        await self._producer.publish(new_event)

        return IngestEventResponseDTO(event_id=new_event.event_id)
