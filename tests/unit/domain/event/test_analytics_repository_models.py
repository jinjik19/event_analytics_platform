from datetime import date
from uuid import UUID

import pytest

from domain.event.repository import (
    EventCountByDay,
    EventFunnelParams,
    EventFunnelResult,
    EventRetentionParams,
    EventRetentionResult,
    EventTopCountriesParams,
    EventTopCountriesResult,
    EventTopProductsParams,
    EventTopProductsResult,
)
from domain.event.types import AnalyticsMetrics, CountriesMetrics, EventType
from domain.utils.generate_uuid import generate_uuid


class TestEventCountByDay:
    def test_create_valid(self):
        record = EventCountByDay(date=date(2026, 3, 1), count=42)

        assert record.date == date(2026, 3, 1)
        assert record.count == 42

    def test_is_frozen(self):
        record = EventCountByDay(date=date(2026, 3, 1), count=10)

        with pytest.raises(Exception):
            record.count = 99  # type: ignore[misc]

    def test_zero_count(self):
        record = EventCountByDay(date=date(2026, 3, 1), count=0)

        assert record.count == 0


class TestEventFunnelParams:
    def test_create_valid(self):
        project_id = generate_uuid()
        params = EventFunnelParams(
            project_id=project_id,
            steps=[EventType.PAGE_VIEW, EventType.PURCHASE],
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            window_days=7,
        )

        assert params.project_id == project_id
        assert params.steps == [EventType.PAGE_VIEW, EventType.PURCHASE]
        assert params.date_from == date(2026, 1, 1)
        assert params.date_to == date(2026, 1, 31)
        assert params.window_days == 7

    def test_is_mutable(self):
        project_id = generate_uuid()
        params = EventFunnelParams(
            project_id=project_id,
            steps=[EventType.PAGE_VIEW],
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            window_days=7,
        )

        params.window_days = 14

        assert params.window_days == 14

    def test_supports_all_event_types_as_steps(self):
        project_id = generate_uuid()
        all_steps = list(EventType)
        params = EventFunnelParams(
            project_id=project_id,
            steps=all_steps,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            window_days=7,
        )

        assert params.steps == all_steps


class TestEventFunnelResult:
    def test_create_with_conversions(self):
        result = EventFunnelResult(
            step=EventType.PURCHASE,
            users=150,
            conversion_from_prev=0.5,
            conversion_from_top=0.15,
        )

        assert result.step == EventType.PURCHASE
        assert result.users == 150
        assert result.conversion_from_prev == 0.5
        assert result.conversion_from_top == 0.15

    def test_create_with_none_conversions(self):
        result = EventFunnelResult(
            step=EventType.PAGE_VIEW,
            users=1000,
            conversion_from_prev=None,
            conversion_from_top=None,
        )

        assert result.conversion_from_prev is None
        assert result.conversion_from_top is None

    def test_is_frozen(self):
        result = EventFunnelResult(
            step=EventType.PAGE_VIEW,
            users=1000,
            conversion_from_prev=None,
            conversion_from_top=None,
        )

        with pytest.raises(Exception):
            result.users = 999  # type: ignore[misc]


class TestEventTopProductsParams:
    def test_create_valid(self):
        project_id = generate_uuid()
        params = EventTopProductsParams(
            project_id=project_id,
            metric=AnalyticsMetrics.BY_REVENUE,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            limit=10,
        )

        assert params.project_id == project_id
        assert params.metric == AnalyticsMetrics.BY_REVENUE
        assert params.limit == 10

    def test_supports_both_metrics(self):
        project_id = generate_uuid()

        for metric in AnalyticsMetrics:
            params = EventTopProductsParams(
                project_id=project_id,
                metric=metric,
                date_from=date(2026, 1, 1),
                date_to=date(2026, 1, 31),
                limit=10,
            )
            assert params.metric == metric


class TestEventTopProductsResult:
    def test_create_valid(self):
        result = EventTopProductsResult(
            category="Electronics",
            product_id="prod-001",
            product_name="Laptop",
            add_to_cart_count=300,
            purchase_count=150,
            revenue=75000.0,
        )

        assert result.category == "Electronics"
        assert result.product_id == "prod-001"
        assert result.product_name == "Laptop"
        assert result.add_to_cart_count == 300
        assert result.purchase_count == 150
        assert result.revenue == 75000.0

    def test_is_frozen(self):
        result = EventTopProductsResult(
            category="X",
            product_id="x-1",
            product_name="X",
            add_to_cart_count=1,
            purchase_count=1,
            revenue=1.0,
        )

        with pytest.raises(Exception):
            result.revenue = 999.0  # type: ignore[misc]

    def test_zero_revenue_and_counts(self):
        result = EventTopProductsResult(
            category="Free",
            product_id="free-1",
            product_name="Free Item",
            add_to_cart_count=0,
            purchase_count=0,
            revenue=0.0,
        )

        assert result.revenue == 0.0
        assert result.add_to_cart_count == 0


class TestEventRetentionParams:
    def test_create_valid(self):
        project_id = generate_uuid()
        params = EventRetentionParams(
            project_id=project_id,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            days=30,
        )

        assert params.project_id == project_id
        assert params.days == 30

    def test_is_mutable(self):
        project_id = generate_uuid()
        params = EventRetentionParams(
            project_id=project_id,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            days=30,
        )

        params.days = 7

        assert params.days == 7


class TestEventRetentionResult:
    def test_create_day_zero(self):
        result = EventRetentionResult(
            cohort_date=date(2026, 1, 1),
            day_number=0,
            retained_users=500,
            cohort_size=500,
            retention_pct=100.0,
        )

        assert result.day_number == 0
        assert result.retention_pct == 100.0

    def test_create_subsequent_day(self):
        result = EventRetentionResult(
            cohort_date=date(2026, 1, 1),
            day_number=30,
            retained_users=100,
            cohort_size=500,
            retention_pct=20.0,
        )

        assert result.day_number == 30
        assert result.retained_users == 100
        assert result.cohort_size == 500

    def test_is_frozen(self):
        result = EventRetentionResult(
            cohort_date=date(2026, 1, 1),
            day_number=1,
            retained_users=200,
            cohort_size=500,
            retention_pct=40.0,
        )

        with pytest.raises(Exception):
            result.retention_pct = 99.0  # type: ignore[misc]


class TestEventTopCountriesParams:
    def test_create_valid(self):
        project_id = generate_uuid()
        params = EventTopCountriesParams(
            project_id=project_id,
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 31),
            limit=10,
            sort_by=CountriesMetrics.BY_USERS,
        )

        assert params.project_id == project_id
        assert params.limit == 10
        assert params.sort_by == CountriesMetrics.BY_USERS

    def test_supports_all_sort_by_metrics(self):
        project_id = generate_uuid()

        for metric in CountriesMetrics:
            params = EventTopCountriesParams(
                project_id=project_id,
                date_from=date(2026, 1, 1),
                date_to=date(2026, 1, 31),
                limit=10,
                sort_by=metric,
            )
            assert params.sort_by == metric


class TestEventTopCountriesResult:
    def test_create_valid(self):
        result = EventTopCountriesResult(
            country="US",
            unique_users=5000,
            events_count=20000,
            revenue=100000.0,
        )

        assert result.country == "US"
        assert result.unique_users == 5000
        assert result.events_count == 20000
        assert result.revenue == 100000.0

    def test_is_frozen(self):
        result = EventTopCountriesResult(
            country="US",
            unique_users=5000,
            events_count=20000,
            revenue=100000.0,
        )

        with pytest.raises(Exception):
            result.country = "DE"  # type: ignore[misc]

    def test_zero_revenue(self):
        result = EventTopCountriesResult(
            country="XX",
            unique_users=1,
            events_count=1,
            revenue=0.0,
        )

        assert result.revenue == 0.0
