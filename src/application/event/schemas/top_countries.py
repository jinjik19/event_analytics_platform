from datetime import date, timedelta

from pydantic import BaseModel, Field

from domain.event.types import CountriesMetrics


class EventTopCountriesQueryParams(BaseModel):
    date_from: date = Field(default_factory=lambda: date.today() - timedelta(days=30))
    date_to: date = Field(default_factory=date.today)
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: CountriesMetrics = CountriesMetrics.BY_USERS


class EventTopCountriesResponseDTO(BaseModel):
    country: str
    unique_users: int
    events_count: int
    revenue: float
