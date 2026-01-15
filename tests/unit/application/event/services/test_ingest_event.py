from datetime import datetime
from uuid import UUID

from application.event.schemas.ingest_dto import IngestEventDTO, PropertiesDTO, UserPropertiesDTO, DeviceDTO
from application.event.services.ingest import IngestEventService
from domain.utils.generate_uuid import generate_uuid


async def test_ingest_event_service(mock_uow, mock_logger, test_settings):
    service = IngestEventService(logger=mock_logger, settings=test_settings)
    project_id = generate_uuid()
    dto = IngestEventDTO(
        user_id=generate_uuid(),
        session_id=generate_uuid(),
        event_type="test_event",
        timestamp=datetime.now(),
        properties=PropertiesDTO(
            page_url="http://test.com",
        ),
        user_properties=UserPropertiesDTO(
            country="NZ",
        ),
        device=DeviceDTO(
            browser="Chrome",
            os="Windows",
        ),
    )

    result = await service(project_id, dto)

    assert result is not None
    assert isinstance(result, UUID)

    assert mock_logger.info.called
