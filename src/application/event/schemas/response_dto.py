from uuid import UUID

from pydantic import BaseModel


class IngestEventResponseDTO(BaseModel):
    status: str = "accepted"
    event_id: UUID
