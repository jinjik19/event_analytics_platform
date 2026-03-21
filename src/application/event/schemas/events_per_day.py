from datetime import date

from pydantic import BaseModel


class EventsPerDayResponseDTO(BaseModel):
    date: date
    count: int
