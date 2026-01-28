from datetime import datetime, timedelta, timezone
import os
import random
from typing import Any

import structlog

from src.domain.project.types import Plan
from src.domain.event.types import EventType
from tests.load.helpers import generate_random_string, generate_session_id, generate_timestamp, generate_user_id


logger = structlog.get_logger("load_test")

PROJECT_NAME_PREFIX = os.getenv("PROJECT_NAME_PREFIX", "load_test")
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "test-secret-token")


def setup_projects(host: str) -> list[str]:
    """Helper to create projects via `requests` (synchronous) before test starts."""
    import requests

    created_keys = []
    plans = [
        Plan.PRO,
        Plan.ENTERPRISE,
        Plan.ENTERPRISE,
        Plan.ENTERPRISE,
        Plan.ENTERPRISE,
        Plan.ENTERPRISE,
    ]

    existing = os.getenv("LOAD_TEST_API_KEY")
    if existing:
        return [existing]

    logger.info("creating_projects_via_requests", host=host)

    for plan in plans:
        try:
            name = f"{PROJECT_NAME_PREFIX}_{plan}_{random.randint(1000,9999)}"
            resp = requests.post(
                f"{host}/api/v1/project",
                json={"name": name, "plan": plan},
                headers={"Authorization": f"Bearer {SECRET_TOKEN}"},
                timeout=5
            )
            if resp.status_code == 200:
                key = resp.json().get("api_key")
                if key:
                    created_keys.append(key)
            else:
                logger.error("project_create_failed", status=resp.status_code, text=resp.text)
        except Exception as e:
            logger.error("setup_connection_error", error=str(e))

    return created_keys


def generate_product_id() -> str:
    """Generate product_id."""
    return f"prod_{generate_random_string(8)}"


def generate_page_view_event() -> dict[str, Any]:
    """Generate PAGE_VIEW event. No required properties."""
    return {
        "user_id": generate_user_id(),
        "session_id": generate_session_id(),
        "event_type": EventType.PAGE_VIEW,
        "timestamp": generate_timestamp(),
        "properties": {
            "page_url": f"https://example.com/page/{generate_random_string(5)}",
            "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
            "os": random.choice(["Windows", "macOS", "Linux", "iOS", "Android"]),
            "device_type": random.choice(["desktop", "mobile", "tablet"]),
            "country": random.choice(["US", "GB", "DE", "FR", "JP", "RU"]),
            "source": random.choice(["organic", "paid", "social", "email", None]),
        }
    }


def generate_product_view_event() -> dict[str, Any]:
    """Generate PRODUCT_VIEW event. Requires product_id."""
    return {
        "user_id": generate_user_id(),
        "session_id": generate_session_id(),
        "event_type": EventType.PRODUCT_VIEW,
        "timestamp": generate_timestamp(),
        "properties": {
            "page_url": f"https://example.com/products/{generate_random_string(5)}",
            "product_id": generate_product_id(),
            "product_name": f"Product {generate_random_string(5)}",
            "category": random.choice(["Electronics", "Clothing", "Books", "Home"]),
            "price": round(random.uniform(10.0, 999.99), 2),
            "currency": random.choice(["USD", "EUR", "GBP", "RUB"]),
            "browser": random.choice(["Chrome", "Firefox", "Safari"]),
            "device_type": random.choice(["desktop", "mobile", "tablet"]),
        }
    }


def generate_add_to_cart_event() -> dict[str, Any]:
    """Generate ADD_TO_CART event. Requires product_id."""
    return {
        "user_id": generate_user_id(),
        "session_id": generate_session_id(),
        "event_type": EventType.ADD_TO_CART,
        "timestamp": generate_timestamp(),
        "properties": {
            "product_id": generate_product_id(),
            "product_name": f"Product {generate_random_string(5)}",
            "category": random.choice(["Electronics", "Clothing", "Books"]),
            "price": round(random.uniform(10.0, 999.99), 2),
            "quantity": random.randint(1, 5),
            "currency": "USD",
            "button_clicked": "add_to_cart_button",
        }
    }


def generate_remove_from_cart_event() -> dict[str, Any]:
    """Generate REMOVE_FROM_CART event. Requires product_id."""
    return {
        "user_id": generate_user_id(),
        "session_id": generate_session_id(),
        "event_type": EventType.REMOVE_FROM_CART,
        "timestamp": generate_timestamp(),
        "properties": {
            "product_id": generate_product_id(),
            "quantity": random.randint(1, 3),
            "button_clicked": "remove_from_cart_button",
        }
    }


def generate_purchase_event() -> dict[str, Any]:
    """Generate PURCHASE event. Requires product_id, price, quantity."""
    return {
        "user_id": generate_user_id(),
        "session_id": generate_session_id(),
        "event_type": EventType.PURCHASE,
        "timestamp": generate_timestamp(),
        "properties": {
            "product_id": generate_product_id(),
            "product_name": f"Product {generate_random_string(5)}",
            "category": random.choice(["Electronics", "Clothing", "Books", "Home"]),
            "price": round(random.uniform(10.0, 999.99), 2),
            "quantity": random.randint(1, 10),
            "currency": "USD",
            "country": random.choice(["US", "GB", "DE"]),
        }
    }


def generate_random_event() -> dict[str, Any]:
    """
    Generate random event with realistic distribution.

    Distribution:
    - PAGE_VIEW: 50%
    - PRODUCT_VIEW: 25%
    - ADD_TO_CART: 15%
    - PURCHASE: 7%
    - REMOVE_FROM_CART: 3%
    """
    r = random.random()
    if r < 0.50:
        return generate_page_view_event()
    elif r < 0.75:
        return generate_product_view_event()
    elif r < 0.90:
        return generate_add_to_cart_event()
    elif r < 0.97:
        return generate_purchase_event()
    return generate_remove_from_cart_event()


def generate_invalid_event(error_type: str = "random") -> dict[str, Any]:
    """
    Generate intentionally invalid event for error testing.

    Error types:
    - missing_event_type: missing required field
    - invalid_event_type: invalid event_type value
    - future_timestamp: timestamp in future
    - old_timestamp: timestamp older than 30 days
    - missing_required_props: missing required properties for event type
    - invalid_price: negative or too large price
    """
    if error_type == "random":
        error_type = random.choice([
            "missing_event_type",
            "invalid_event_type",
            "future_timestamp",
            "old_timestamp",
            "missing_required_props",
            "invalid_price",
        ])

    match error_type:
        case "missing_event_type":
            return {
                "user_id": generate_user_id(),
                "session_id": generate_session_id(),
                "timestamp": generate_timestamp(),
                "properties": {"page_url": "https://example.com"},
            }
        case "invalid_event_type":
            return {
                "user_id": generate_user_id(),
                "session_id": generate_session_id(),
                "event_type": "INVALID_TYPE",
                "timestamp": generate_timestamp(),
                "properties": {"page_url": "https://example.com"},
            }
        case "future_timestamp":
            future = datetime.now(timezone.utc) + timedelta(hours=1)
            return {
                "user_id": generate_user_id(),
                "session_id": generate_session_id(),
                "event_type": EventType.PAGE_VIEW,
                "timestamp": future.isoformat(),
                "properties": {"page_url": "https://example.com"},
            }
        case "old_timestamp":
            old = datetime.now(timezone.utc) - timedelta(days=60)
            return {
                "user_id": generate_user_id(),
                "session_id": generate_session_id(),
                "event_type": EventType.PAGE_VIEW,
                "timestamp": old.isoformat(),
                "properties": {"page_url": "https://example.com"},
            }
        case "missing_required_props":
            # PURCHASE requires product_id, price, quantity
            return {
                "user_id": generate_user_id(),
                "session_id": generate_session_id(),
                "event_type": EventType.PURCHASE,
                "timestamp": generate_timestamp(),
                "properties": {"page_url": "https://example.com"},
            }
        case "invalid_price":
            return {
                "user_id": generate_user_id(),
                "session_id": generate_session_id(),
                "event_type": EventType.PURCHASE,
                "timestamp": generate_timestamp(),
                "properties": {
                    "product_id": generate_product_id(),
                    "price": -100.0,  # Invalid negative price
                    "quantity": 1,
                },
            }

    return generate_page_view_event()


def generate_batch_events(count: int = 10, include_invalid: bool = False) -> list[dict[str, Any]]:
    """
    Generate batch of events.

    Args:
        count: Number of events in batch
        include_invalid: Include invalid events (for filtering test)
    """
    events_list = []
    for i in range(count):
        if include_invalid and i % 5 == 0:
            events_list.append(generate_invalid_event())
        else:
            events_list.append(generate_random_event())
    return events_list
