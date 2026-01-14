from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PropertiesDTO(BaseModel):
    page_url: str | None
    button_clicked: str | None


class UserPropertiesDTO(BaseModel):
    country: str | None


class DeviceDTO(BaseModel):
    browser: str | None
    os: str | None


class IngestEventDTO(BaseModel):
    user_id: UUID | None
    session_id: UUID | None
    event_type: str
    timestamp: datetime
    properties: PropertiesDTO
    user_properties: UserPropertiesDTO
    device: DeviceDTO
