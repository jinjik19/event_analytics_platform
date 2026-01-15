from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PropertiesDTO(BaseModel):
    page_url: str | None = None
    button_clicked: str | None = None


class UserPropertiesDTO(BaseModel):
    country: str | None = None


class DeviceDTO(BaseModel):
    browser: str | None = None
    os: str | None = None


class IngestEventDTO(BaseModel):
    user_id: UUID | None = None
    session_id: UUID | None = None
    event_type: str
    timestamp: datetime
    properties: PropertiesDTO
    user_properties: UserPropertiesDTO
    device: DeviceDTO
