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
