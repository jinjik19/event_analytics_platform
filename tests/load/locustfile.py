import random

from locust import between, tag, task

from tests.load.base import AnalyticsBaseUser
from tests.load.data_generator import (
    generate_batch_events,
    generate_page_view_event,
    generate_product_view_event,
    generate_add_to_cart_event,
    generate_remove_from_cart_event,
    generate_purchase_event,
)


class SingleEventUser(AnalyticsBaseUser):
    """
    User for verifying Rate Limits or simple single-endpoint latency.
    Useful when running with specific API Keys (e.g. FREE plan) via env var.

    Command:
    export LOAD_TEST_API_KEY="wk_free_..."
    locust -f tests/load/locustfile.py --tags rate_limit
    """
    wait_time = between(0.1, 0.5)
    weight = 1

    @task
    @tag("single", "rate_limit")
    def send_simple_event(self):
        """
        Sends cheap Page View events rapidly to trigger 429.
        """
        payload = generate_page_view_event()
        self.post_event("/api/v1/event", payload, "POST /event (Single)")


class MixedLoadUser(AnalyticsBaseUser):
    """
    Real production traffic simulator (E-commerce Funnel).
    Total weights = 100 for easy probability calculation.
    """
    wait_time = between(1, 3) # Имитируем раздумья пользователя
    weight = 100

    @task(40)
    @tag("view", "page")
    def send_page_view(self):
        """Top of funnel: Browsing pages"""
        payload = generate_page_view_event()
        self.post_event("/api/v1/event", payload, "POST /event (Page View)")

    @task(30)
    @tag("view", "product")
    def send_product_view(self):
        """Middle of funnel: Viewing specific products"""
        payload = generate_product_view_event()
        self.post_event("/api/v1/event", payload, "POST /event (Product View)")

    @task(10)
    @tag("cart", "add")
    def send_add_to_cart(self):
        """Intent: Adding to cart"""
        payload = generate_add_to_cart_event()
        self.post_event("/api/v1/event", payload, "POST /event (Add to Cart)")

    @task(5)
    @tag("cart", "remove")
    def send_remove_from_cart(self):
        """Churn: Removing from cart"""
        payload = generate_remove_from_cart_event()
        self.post_event("/api/v1/event", payload, "POST /event (Remove from Cart)")

    @task(5)
    @tag("conversion", "purchase")
    def send_purchase(self):
        """Bottom of funnel: Purchase (Conversion)"""
        payload = generate_purchase_event()
        self.post_event("/api/v1/event", payload, "POST /event (Purchase)")

    @task(10)
    @tag("batch", "background")
    def send_background_batch(self):
        """
        Simulates mobile app background sync or frontend batching.
        Sending small batches of mixed events.
        """
        # Генерируем небольшой батч (5-15 событий)
        events = generate_batch_events(count=random.randint(5, 15))
        self.post_event("/api/v1/event/batch", {"events": events}, "POST /event/batch (Small)")


class StressBatchUser(AnalyticsBaseUser):
    """
    High throughput user.
    Uses large mixed batches to stress test DB write throughput.
    """
    wait_time = between(0.1, 0.5) # Агрессивный режим
    weight = 10

    @task
    @tag("stress")
    def heavy_mixed_batch(self):
        """
        Sends heavy batches (200 events).
        generate_batch_events already mixes different event types randomly,
        so we are stressing the DB with diverse data.
        """
        events = generate_batch_events(count=200)
        self.post_event("/api/v1/event/batch", {"events": events}, "POST /event/batch (Stress)")
