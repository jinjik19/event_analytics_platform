from uuid import UUID

from structlog import BoundLogger

from application.event.schemas.ingest_dto import IngestEventBatchDTO
from application.event.schemas.response_dto import IngestEventBatchResponseDTO
from domain.event.models import Event
from domain.event.producer import EventProducer
from infrastructure.config.settings import Settings


class IngestEventBatchService:
    def __init__(self, producer: EventProducer, logger: BoundLogger, settings: Settings) -> None:
        self._producer = producer
        self._logger = logger
        self._settings = settings

    async def __call__(
        self, project_id: UUID, data: IngestEventBatchDTO
    ) -> IngestEventBatchResponseDTO:
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

        await self._producer.publish_batch(new_events)

        return IngestEventBatchResponseDTO(event_ids=[event.event_id for event in new_events])
