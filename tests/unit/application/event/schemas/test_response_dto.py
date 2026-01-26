from uuid import UUID

import pytest

from application.event.schemas.response_dto import IngestEventBatchResponseDTO, IngestEventResponseDTO
from domain.utils.generate_uuid import generate_uuid


class TestIngestEventResponseDTO:
    def test_default_status(self):
        event_id = generate_uuid()

        dto = IngestEventResponseDTO(event_id=event_id)

        assert dto.status == "accepted"
        assert dto.event_id == event_id

    def test_custom_status(self):
        event_id = generate_uuid()

        dto = IngestEventResponseDTO(status="processed", event_id=event_id)

        assert dto.status == "processed"

    def test_event_id_type(self):
        event_id = generate_uuid()

        dto = IngestEventResponseDTO(event_id=event_id)

        assert isinstance(dto.event_id, UUID)


class TestIngestEventBatchResponseDTO:
    def test_default_status(self):
        event_ids = [generate_uuid(), generate_uuid()]

        dto = IngestEventBatchResponseDTO(event_ids=event_ids)

        assert dto.status == "accepted"
        assert dto.event_ids == event_ids

    def test_custom_status(self):
        event_ids = [generate_uuid()]

        dto = IngestEventBatchResponseDTO(status="processed", event_ids=event_ids)

        assert dto.status == "processed"

    def test_empty_event_ids(self):
        dto = IngestEventBatchResponseDTO(event_ids=[])

        assert dto.status == "accepted"
        assert dto.event_ids == []
        assert len(dto.event_ids) == 0

    def test_single_event_id(self):
        event_id = generate_uuid()

        dto = IngestEventBatchResponseDTO(event_ids=[event_id])

        assert len(dto.event_ids) == 1
        assert dto.event_ids[0] == event_id

    def test_multiple_event_ids(self):
        event_ids = [generate_uuid() for _ in range(10)]

        dto = IngestEventBatchResponseDTO(event_ids=event_ids)

        assert len(dto.event_ids) == 10
        assert all(isinstance(eid, UUID) for eid in dto.event_ids)

    def test_event_ids_are_unique(self):
        event_ids = [generate_uuid() for _ in range(5)]

        dto = IngestEventBatchResponseDTO(event_ids=event_ids)

        assert len(set(dto.event_ids)) == 5

    def test_serialization_to_dict(self):
        event_ids = [generate_uuid(), generate_uuid()]

        dto = IngestEventBatchResponseDTO(event_ids=event_ids)
        data = dto.model_dump()

        assert data["status"] == "accepted"
        assert len(data["event_ids"]) == 2

    def test_serialization_to_json(self):
        event_ids = [generate_uuid(), generate_uuid()]

        dto = IngestEventBatchResponseDTO(event_ids=event_ids)
        json_str = dto.model_dump_json()

        assert "accepted" in json_str
        assert str(event_ids[0]) in json_str
        assert str(event_ids[1]) in json_str
