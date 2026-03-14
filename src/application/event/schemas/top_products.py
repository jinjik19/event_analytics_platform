from datetime import date, timedelta

from pydantic import BaseModel, Field

from domain.event.types import AnalyticsMetrics


class EventTopProductsQueryParams(BaseModel):
    metric: AnalyticsMetrics
    date_from: date = Field(default_factory=lambda: date.today() - timedelta(days=30))
    date_to: date = Field(default_factory=date.today)
    limit: int = Field(default=10, ge=1, le=100)


class EventTopProductsResponseDTO(BaseModel):
    category: str
    product_id: str
    product_name: str
    add_to_cart_count: int
    purchase_count: int
    revenue: float
