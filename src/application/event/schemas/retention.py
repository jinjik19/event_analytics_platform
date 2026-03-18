from datetime import date, timedelta

from pydantic import BaseModel, Field


class EventRetentionQueryParams(BaseModel):
    date_from: date = Field(default_factory=lambda: date.today() - timedelta(days=30))
    date_to: date = Field(default_factory=date.today)
    days: int = Field(default=30, ge=0, le=365)


class EventRetentionResponseDTO(BaseModel):
    cohort_date: date
    day_number: int
    retained_users: int
    cohort_size: int
    retention_pct: float
