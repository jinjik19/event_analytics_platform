from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from application.event.schemas.events_per_day import EventsPerDayResponseDTO
from application.event.schemas.funnel import EventFunnelQueryParams, EventFunnelResponseDTO
from application.event.schemas.retention import EventRetentionQueryParams, EventRetentionResponseDTO
from application.event.schemas.top_countries import (
    EventTopCountriesQueryParams,
    EventTopCountriesResponseDTO,
)
from application.event.schemas.top_products import (
    EventTopProductsQueryParams,
    EventTopProductsResponseDTO,
)
from domain.event.types import AnalyticsMetrics, CountriesMetrics, EventType


class TestEventsPerDayResponseDTO:
    def test_valid_fields(self):
        dto = EventsPerDayResponseDTO(date=date(2026, 3, 1), count=42)

        assert dto.date == date(2026, 3, 1)
        assert dto.count == 42

    def test_zero_count_is_valid(self):
        dto = EventsPerDayResponseDTO(date=date(2026, 3, 1), count=0)

        assert dto.count == 0

    def test_serialization_to_json_mode(self):
        dto = EventsPerDayResponseDTO(date=date(2026, 3, 1), count=100)
        data = dto.model_dump(mode="json")

        assert data["date"] == "2026-03-01"
        assert data["count"] == 100

    def test_deserialization_from_dict(self):
        dto = EventsPerDayResponseDTO(**{"date": "2026-03-01", "count": 55})

        assert dto.date == date(2026, 3, 1)
        assert dto.count == 55

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            EventsPerDayResponseDTO(date=date(2026, 3, 1))  # type: ignore[call-arg]


class TestEventFunnelQueryParams:
    def test_default_steps(self):
        params = EventFunnelQueryParams()

        assert EventType.PAGE_VIEW in params.steps
        assert EventType.PRODUCT_VIEW in params.steps
        assert EventType.ADD_TO_CART in params.steps
        assert EventType.PURCHASE in params.steps

    def test_default_date_range_is_last_30_days(self):
        params = EventFunnelQueryParams()
        today = date.today()

        assert params.date_to == today
        assert params.date_from == today - timedelta(days=30)

    def test_default_window_days(self):
        params = EventFunnelQueryParams()

        assert params.window_days == 7

    def test_custom_steps(self):
        steps = [EventType.PAGE_VIEW, EventType.PURCHASE]
        params = EventFunnelQueryParams(steps=steps)

        assert params.steps == steps

    def test_custom_date_range(self):
        date_from = date(2026, 1, 1)
        date_to = date(2026, 1, 31)
        params = EventFunnelQueryParams(date_from=date_from, date_to=date_to)

        assert params.date_from == date_from
        assert params.date_to == date_to

    def test_custom_window_days(self):
        params = EventFunnelQueryParams(window_days=14)

        assert params.window_days == 14


class TestEventFunnelResponseDTO:
    def test_valid_fields(self):
        dto = EventFunnelResponseDTO(
            step=EventType.PAGE_VIEW,
            users=1000,
            conversion_from_prev=None,
            conversion_from_top=None,
        )

        assert dto.step == EventType.PAGE_VIEW
        assert dto.users == 1000
        assert dto.conversion_from_prev is None
        assert dto.conversion_from_top is None

    def test_with_conversion_rates(self):
        dto = EventFunnelResponseDTO(
            step=EventType.PURCHASE,
            users=200,
            conversion_from_prev=0.5,
            conversion_from_top=0.2,
        )

        assert dto.conversion_from_prev == 0.5
        assert dto.conversion_from_top == 0.2

    def test_serialization_roundtrip(self):
        dto = EventFunnelResponseDTO(
            step=EventType.ADD_TO_CART,
            users=500,
            conversion_from_prev=0.75,
            conversion_from_top=0.5,
        )
        data = dto.model_dump(mode="json")
        restored = EventFunnelResponseDTO(**data)

        assert restored.step == dto.step
        assert restored.users == dto.users
        assert restored.conversion_from_prev == dto.conversion_from_prev


class TestEventTopProductsQueryParams:
    def test_required_metric_field(self):
        with pytest.raises(ValidationError):
            EventTopProductsQueryParams()  # type: ignore[call-arg]

    def test_valid_by_cart_metric(self):
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART)

        assert params.metric == AnalyticsMetrics.BY_CART

    def test_valid_by_revenue_metric(self):
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_REVENUE)

        assert params.metric == AnalyticsMetrics.BY_REVENUE

    def test_default_limit(self):
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART)

        assert params.limit == 10

    def test_default_date_range(self):
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART)
        today = date.today()

        assert params.date_to == today
        assert params.date_from == today - timedelta(days=30)

    def test_limit_min_boundary(self):
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART, limit=1)

        assert params.limit == 1

    def test_limit_max_boundary(self):
        params = EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART, limit=100)

        assert params.limit == 100

    def test_limit_below_min_raises(self):
        with pytest.raises(ValidationError):
            EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART, limit=0)

    def test_limit_above_max_raises(self):
        with pytest.raises(ValidationError):
            EventTopProductsQueryParams(metric=AnalyticsMetrics.BY_CART, limit=101)

    def test_invalid_metric_raises(self):
        with pytest.raises(ValidationError):
            EventTopProductsQueryParams(metric="invalid_metric")  # type: ignore[arg-type]


class TestEventTopProductsResponseDTO:
    def test_valid_fields(self):
        dto = EventTopProductsResponseDTO(
            category="Electronics",
            product_id="prod-001",
            product_name="Laptop",
            add_to_cart_count=150,
            purchase_count=80,
            revenue=12000.50,
        )

        assert dto.category == "Electronics"
        assert dto.product_id == "prod-001"
        assert dto.product_name == "Laptop"
        assert dto.add_to_cart_count == 150
        assert dto.purchase_count == 80
        assert dto.revenue == 12000.50

    def test_zero_revenue(self):
        dto = EventTopProductsResponseDTO(
            category="Books",
            product_id="book-001",
            product_name="Python Cookbook",
            add_to_cart_count=10,
            purchase_count=0,
            revenue=0.0,
        )

        assert dto.revenue == 0.0
        assert dto.purchase_count == 0

    def test_serialization_to_json_mode(self):
        dto = EventTopProductsResponseDTO(
            category="Clothing",
            product_id="shirt-01",
            product_name="T-Shirt",
            add_to_cart_count=200,
            purchase_count=100,
            revenue=999.99,
        )
        data = dto.model_dump(mode="json")

        assert data["category"] == "Clothing"
        assert data["revenue"] == 999.99


class TestEventRetentionQueryParams:
    def test_default_values(self):
        params = EventRetentionQueryParams()
        today = date.today()

        assert params.date_to == today
        assert params.date_from == today - timedelta(days=30)
        assert params.days == 30

    def test_custom_days(self):
        params = EventRetentionQueryParams(days=7)

        assert params.days == 7

    def test_days_min_boundary(self):
        params = EventRetentionQueryParams(days=0)

        assert params.days == 0

    def test_days_max_boundary(self):
        params = EventRetentionQueryParams(days=365)

        assert params.days == 365

    def test_days_below_min_raises(self):
        with pytest.raises(ValidationError):
            EventRetentionQueryParams(days=-1)

    def test_days_above_max_raises(self):
        with pytest.raises(ValidationError):
            EventRetentionQueryParams(days=366)

    def test_custom_date_range(self):
        date_from = date(2026, 1, 1)
        date_to = date(2026, 1, 31)
        params = EventRetentionQueryParams(date_from=date_from, date_to=date_to)

        assert params.date_from == date_from
        assert params.date_to == date_to


class TestEventRetentionResponseDTO:
    def test_valid_fields(self):
        dto = EventRetentionResponseDTO(
            cohort_date=date(2026, 1, 1),
            day_number=7,
            retained_users=150,
            cohort_size=500,
            retention_pct=30.0,
        )

        assert dto.cohort_date == date(2026, 1, 1)
        assert dto.day_number == 7
        assert dto.retained_users == 150
        assert dto.cohort_size == 500
        assert dto.retention_pct == 30.0

    def test_day_zero(self):
        dto = EventRetentionResponseDTO(
            cohort_date=date(2026, 1, 1),
            day_number=0,
            retained_users=500,
            cohort_size=500,
            retention_pct=100.0,
        )

        assert dto.day_number == 0
        assert dto.retention_pct == 100.0

    def test_serialization_to_json_mode(self):
        dto = EventRetentionResponseDTO(
            cohort_date=date(2026, 1, 1),
            day_number=14,
            retained_users=75,
            cohort_size=300,
            retention_pct=25.0,
        )
        data = dto.model_dump(mode="json")

        assert data["cohort_date"] == "2026-01-01"
        assert data["retention_pct"] == 25.0


class TestEventTopCountriesQueryParams:
    def test_default_values(self):
        params = EventTopCountriesQueryParams()
        today = date.today()

        assert params.date_to == today
        assert params.date_from == today - timedelta(days=30)
        assert params.limit == 10
        assert params.sort_by == CountriesMetrics.BY_USERS

    def test_valid_sort_by_events(self):
        params = EventTopCountriesQueryParams(sort_by=CountriesMetrics.BY_EVENTS)

        assert params.sort_by == CountriesMetrics.BY_EVENTS

    def test_valid_sort_by_revenue(self):
        params = EventTopCountriesQueryParams(sort_by=CountriesMetrics.BY_REVENUE)

        assert params.sort_by == CountriesMetrics.BY_REVENUE

    def test_limit_min_boundary(self):
        params = EventTopCountriesQueryParams(limit=1)

        assert params.limit == 1

    def test_limit_max_boundary(self):
        params = EventTopCountriesQueryParams(limit=100)

        assert params.limit == 100

    def test_limit_below_min_raises(self):
        with pytest.raises(ValidationError):
            EventTopCountriesQueryParams(limit=0)

    def test_limit_above_max_raises(self):
        with pytest.raises(ValidationError):
            EventTopCountriesQueryParams(limit=101)

    def test_invalid_sort_by_raises(self):
        with pytest.raises(ValidationError):
            EventTopCountriesQueryParams(sort_by="invalid")  # type: ignore[arg-type]


class TestEventTopCountriesResponseDTO:
    def test_valid_fields(self):
        dto = EventTopCountriesResponseDTO(
            country="US",
            unique_users=5000,
            events_count=20000,
            revenue=150000.00,
        )

        assert dto.country == "US"
        assert dto.unique_users == 5000
        assert dto.events_count == 20000
        assert dto.revenue == 150000.00

    def test_zero_revenue(self):
        dto = EventTopCountriesResponseDTO(
            country="NZ",
            unique_users=10,
            events_count=50,
            revenue=0.0,
        )

        assert dto.revenue == 0.0

    def test_serialization_to_json_mode(self):
        dto = EventTopCountriesResponseDTO(
            country="DE",
            unique_users=1000,
            events_count=5000,
            revenue=88888.88,
        )
        data = dto.model_dump(mode="json")

        assert data["country"] == "DE"
        assert data["unique_users"] == 1000

    def test_deserialization_from_dict(self):
        dto = EventTopCountriesResponseDTO(
            **{"country": "FR", "unique_users": 200, "events_count": 800, "revenue": 1500.0}
        )

        assert dto.country == "FR"
