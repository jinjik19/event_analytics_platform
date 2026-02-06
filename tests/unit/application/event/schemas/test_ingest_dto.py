from datetime import UTC, datetime

from pydantic import ValidationError
import pytest

from application.event.schemas.ingest_dto import IngestEventDTO, PropertiesDTO
from domain.event.models import Properties
from domain.event.types import EventType


class TestPropertiesConversion:
    def test_price_float_to_int_conversion(self):
        dto = PropertiesDTO(
            product_id="p1",
            price=12.50
        )

        domain = dto.to_domain()

        assert domain.price == 1250
        assert isinstance(domain.price, int)

    def test_price_precision_handling(self):
        dto = PropertiesDTO(price=10.99)
        domain = dto.to_domain()

        assert domain.price == 1099
        assert isinstance(domain.price, int)

    def test_empty_fields_conversion(self):
        dto = PropertiesDTO()
        domain = dto.to_domain()

        assert domain.price is None
        assert domain.page_url is None
        assert isinstance(domain, Properties) # Проверка, что вернулся верный датакласс

    def test_url_conversion(self):
        dto = PropertiesDTO(page_url="https://google.com/search")
        domain = dto.to_domain()

        assert domain.page_url == "https://google.com/search"
        assert isinstance(domain.page_url, str)


class TestIngestEventValidation:
    def test_valid_purchase_event(self):
        raw_data = {
            "event_type": "purchase",
            "timestamp": datetime.now(UTC).isoformat(),
            "properties": {
                "product_id": "prod_123",
                "price": 99.90,
                "quantity": 1,
                "currency": "USD",
                "page_url": "https://shop.com/checkout"
            }
        }

        dto = IngestEventDTO(**raw_data)

        # Проверяем DTO
        assert dto.properties.price == 99.90

        # Проверяем конвертацию в домен
        domain_props = dto.properties.to_domain()
        assert domain_props.price == 9990
        assert domain_props.product_id == "prod_123"

    def test_purchase_missing_price(self):
        with pytest.raises(ValidationError) as exc:
            IngestEventDTO(
                event_type=EventType.PURCHASE,
                timestamp=datetime.now(UTC),
                properties=PropertiesDTO(product_id="123", quantity=1)
            )
        assert "PURCHASE requires price" in str(exc.value)

    def test_add_to_cart_requires_product_id(self):
        with pytest.raises(ValidationError) as exc:
            IngestEventDTO(
                event_type=EventType.ADD_TO_CART,
                timestamp=datetime.now(UTC),
                properties=PropertiesDTO(price=10.0)
            )
        assert "requires product_id" in str(exc.value)

    def test_timestamp_auto_utc_conversion(self):
        naive_dt = datetime.now(UTC).replace(tzinfo=None)
        dto = IngestEventDTO(
            event_type=EventType.PAGE_VIEW,
            timestamp=naive_dt,
            properties={}
        )
        assert dto.timestamp.tzinfo == UTC


class TestIngestEventBatchDTO:
    def test_valid_batch_with_all_valid_events(self):
        from application.event.schemas.ingest_dto import IngestEventBatchDTO

        raw_events = [
            {
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"page_url": "https://example.com/page1"},
            },
            {
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"page_url": "https://example.com/page2"},
            },
        ]

        batch = IngestEventBatchDTO(events=raw_events)

        assert len(batch.events) == 2
        assert all(isinstance(e, IngestEventDTO) for e in batch.events)

    def test_batch_filters_invalid_events(self):
        from application.event.schemas.ingest_dto import IngestEventBatchDTO

        raw_events = [
            {
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"page_url": "https://example.com/valid"},
            },
            {
                "event_type": "invalid_type",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {},
            },
            {
                "event_type": "purchase",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {},
            },
        ]

        batch = IngestEventBatchDTO(events=raw_events)

        assert len(batch.events) == 1
        assert batch.events[0].event_type == EventType.PAGE_VIEW

    def test_batch_with_all_invalid_events_returns_empty(self):
        from application.event.schemas.ingest_dto import IngestEventBatchDTO

        raw_events = [
            {"event_type": "invalid", "timestamp": "bad", "properties": {}},
            {"event_type": "purchase", "properties": {}},
        ]

        with pytest.raises(ValidationError):
            IngestEventBatchDTO(events=raw_events)

    def test_batch_with_empty_list(self):
        from application.event.schemas.ingest_dto import IngestEventBatchDTO

        with pytest.raises(ValidationError):
             IngestEventBatchDTO(events=[])

    def test_batch_preserves_valid_purchase_events(self):
        from application.event.schemas.ingest_dto import IngestEventBatchDTO

        raw_events = [
            {
                "event_type": "purchase",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {
                    "product_id": "prod_123",
                    "price": 99.99,
                    "quantity": 2,
                    "currency": "USD",
                },
            },
        ]

        batch = IngestEventBatchDTO(events=raw_events)

        assert len(batch.events) == 1
        assert batch.events[0].event_type == EventType.PURCHASE
        assert batch.events[0].properties.product_id == "prod_123"

    def test_batch_mixed_event_types(self):
        from application.event.schemas.ingest_dto import IngestEventBatchDTO

        raw_events = [
            {
                "event_type": "page_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"page_url": "https://example.com"},
            },
            {
                "event_type": "product_view",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"product_id": "prod_1"},
            },
            {
                "event_type": "add_to_cart",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {"product_id": "prod_1"},
            },
            {
                "event_type": "purchase",
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {
                    "product_id": "prod_1",
                    "price": 50.00,
                    "quantity": 1,
                },
            },
        ]

        batch = IngestEventBatchDTO(events=raw_events)

        assert len(batch.events) == 4
        event_types = [e.event_type for e in batch.events]
        assert EventType.PAGE_VIEW in event_types
        assert EventType.PRODUCT_VIEW in event_types
        assert EventType.ADD_TO_CART in event_types
        assert EventType.PURCHASE in event_types

    def test_batch_non_list_input_passes_through(self):
        from application.event.schemas.ingest_dto import IngestEventBatchDTO

        with pytest.raises(ValidationError):
            IngestEventBatchDTO(events="not a list")
