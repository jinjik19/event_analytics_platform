from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from application.event.schemas.ingest_dto import IngestEventBatchDTO, IngestEventDTO, PropertiesDTO
from application.event.schemas.response_dto import IngestEventBatchResponseDTO
from application.event.services.ingest_batch import IngestEventBatchService
from domain.event.types import EventType
from domain.utils.generate_uuid import generate_uuid


class TestIngestEventBatchService:
    @pytest.fixture
    def service(self, mock_uow, mock_logger, mock_settings):
        mock_uow.event = AsyncMock()
        mock_uow.event.add_many = AsyncMock()
        return IngestEventBatchService(uow=mock_uow, logger=mock_logger, settings=mock_settings)

    @pytest.fixture
    def project_id(self):
        return generate_uuid()

    @pytest.fixture
    def sample_batch_dto(self):
        return IngestEventBatchDTO(
            events=[
                IngestEventDTO(
                    user_id="user_1",
                    session_id="session_1",
                    event_type=EventType.PAGE_VIEW,
                    timestamp=datetime.now(UTC),
                    properties=PropertiesDTO(
                        page_url="https://example.com/page1",
                        country="US",
                        browser="Chrome",
                    ),
                ),
                IngestEventDTO(
                    user_id="user_2",
                    session_id="session_2",
                    event_type=EventType.PRODUCT_VIEW,
                    timestamp=datetime.now(UTC),
                    properties=PropertiesDTO(
                        product_id="prod_123",
                        page_url="https://example.com/product",
                    ),
                ),
            ]
        )

    async def test_ingest_batch_returns_response_dto(
        self, service, project_id, sample_batch_dto
    ):
        result = await service(project_id=project_id, data=sample_batch_dto)

        assert isinstance(result, IngestEventBatchResponseDTO)
        assert result.status == "accepted"

    async def test_ingest_batch_returns_correct_event_ids(
        self, service, project_id, sample_batch_dto
    ):
        result = await service(project_id=project_id, data=sample_batch_dto)

        assert len(result.event_ids) == 2
        assert all(isinstance(eid, UUID) for eid in result.event_ids)

    async def test_ingest_batch_calls_add_many(
        self, service, mock_uow, project_id, sample_batch_dto
    ):
        await service(project_id=project_id, data=sample_batch_dto)

        mock_uow.event.add_many.assert_called_once()
        events_arg = mock_uow.event.add_many.call_args[0][0]
        assert len(events_arg) == 2

    async def test_ingest_batch_commits_transaction(
        self, service, mock_uow, project_id, sample_batch_dto
    ):
        await service(project_id=project_id, data=sample_batch_dto)

        mock_uow.commit.assert_called_once()

    async def test_ingest_batch_logs_info(
        self, service, mock_logger, project_id, sample_batch_dto
    ):
        await service(project_id=project_id, data=sample_batch_dto)

        assert mock_logger.info.call_count == 2
        first_call_kwargs = mock_logger.info.call_args_list[0][1]
        assert first_call_kwargs["events"] == 2
        assert first_call_kwargs["project_id"] == project_id

    async def test_ingest_batch_creates_events_with_correct_project_id(
        self, service, mock_uow, project_id, sample_batch_dto
    ):
        await service(project_id=project_id, data=sample_batch_dto)

        events_arg = mock_uow.event.add_many.call_args[0][0]
        assert all(event.project_id == project_id for event in events_arg)

    async def test_ingest_batch_with_empty_events(
        self, service, mock_uow, project_id
    ):
        empty_batch = IngestEventBatchDTO(events=[])

        result = await service(project_id=project_id, data=empty_batch)

        assert len(result.event_ids) == 0
        mock_uow.event.add_many.assert_called_once_with([])

    async def test_ingest_batch_preserves_event_data(
        self, service, mock_uow, project_id
    ):
        batch_dto = IngestEventBatchDTO(
            events=[
                IngestEventDTO(
                    user_id="specific_user",
                    session_id="specific_session",
                    event_type=EventType.PURCHASE,
                    timestamp=datetime.now(UTC),
                    properties=PropertiesDTO(
                        product_id="prod_456",
                        price=99.99,
                        quantity=3,
                        currency="EUR",
                    ),
                ),
            ]
        )

        await service(project_id=project_id, data=batch_dto)

        events_arg = mock_uow.event.add_many.call_args[0][0]
        event = events_arg[0]
        assert event.user_id == "specific_user"
        assert event.session_id == "specific_session"
        assert event.event_type == EventType.PURCHASE
        assert event.properties.product_id == "prod_456"
        assert event.properties.price == 9999
        assert event.properties.quantity == 3
        assert event.properties.currency == "EUR"

    async def test_ingest_batch_single_event(self, service, project_id):
        single_event_batch = IngestEventBatchDTO(
            events=[
                IngestEventDTO(
                    event_type=EventType.PAGE_VIEW,
                    timestamp=datetime.now(UTC),
                    properties=PropertiesDTO(page_url="https://example.com"),
                ),
            ]
        )

        result = await service(project_id=project_id, data=single_event_batch)

        assert len(result.event_ids) == 1

    async def test_ingest_batch_large_batch(self, service, mock_uow, project_id):
        events = [
            IngestEventDTO(
                user_id=f"user_{i}",
                event_type=EventType.PAGE_VIEW,
                timestamp=datetime.now(UTC),
                properties=PropertiesDTO(page_url=f"https://example.com/page{i}"),
            )
            for i in range(100)
        ]
        large_batch = IngestEventBatchDTO(events=events)

        result = await service(project_id=project_id, data=large_batch)

        assert len(result.event_ids) == 100
        events_arg = mock_uow.event.add_many.call_args[0][0]
        assert len(events_arg) == 100
