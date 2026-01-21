from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

from application.event.schemas.ingest_dto import IngestEventDTO, PropertiesDTO
from application.event.services.ingest import IngestEventService
from domain.event.types import EventType
from domain.utils.generate_uuid import generate_uuid


async def test_ingest_event_service(mock_uow, mock_logger, test_settings):
    mock_uow.event = AsyncMock()
    service = IngestEventService(uow=mock_uow, logger=mock_logger, settings=test_settings)
    project_id = generate_uuid()
    dto = IngestEventDTO(
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        event_type=EventType.PAGE_VIEW,
        timestamp=datetime.now(),
        properties=PropertiesDTO(
            page_url="http://test.com",
            country="NZ",
            browser="Chrome",
            os="Windows",
        ),
    )

    result = await service(project_id, dto)

    assert result is not None
    assert isinstance(result, UUID)

    assert mock_logger.info.called
