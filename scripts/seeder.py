import asyncio
import os
import random
import signal
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import httpx
import structlog
from faker import Faker

from domain.event.types import EventType
from domain.project.types import Plan


logger = structlog.get_logger("seeder")

API_HOST = os.getenv("API_HOST", "http://localhost:8000")
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "test-secret-token")
SPEED_MULTIPLIER = float(os.getenv("SEEDER_SPEED", "1.0"))
NUM_USERS = int(os.getenv("SEEDER_USERS", "5"))

fake = Faker()

PRODUCT_CATALOG = [
    {
        "id": f"prod_{i:04d}",
        "name": fake.catch_phrase(),
        "category": cat,
        "price": round(random.uniform(9.99, 499.99), 2),
    }
    for i, cat in enumerate(["Electronics", "Clothing", "Books", "Home", "Sports", "Beauty"] * 10)
]

PAGES = [
    "/",
    "/products",
    "/categories",
    "/deals",
    "/about",
    "/contact",
    "/blog",
    "/faq",
    "/shipping",
    "/returns",
    "/account",
    "/wishlist",
]


@dataclass
class Project:
    """Project with API key."""

    name: str
    plan: Plan
    api_key: str


@dataclass
class UserSession:
    """Simulated user session state."""

    user_id: str
    session_id: str
    project: Project
    cart: list[dict] = field(default_factory=list)
    viewed_products: list[dict] = field(default_factory=list)
    page_views: int = 0

    def reset(self):
        """Reset session (user left and came back)."""
        self.session_id = f"session_{fake.uuid4()[:16]}"
        self.cart = []
        self.viewed_products = []
        self.page_views = 0


class EventSeeder:
    """Realistic event seeder that simulates user behavior."""

    def __init__(self):
        self.projects: list[Project] = []
        self.running = True
        self.client: httpx.AsyncClient | None = None
        self.stats = {"events_sent": 0, "batches_sent": 0, "errors": 0}

    async def setup(self):
        """Initialize seeder: create HTTP client and projects."""
        self.client = httpx.AsyncClient(base_url=API_HOST, timeout=30.0)

        await self._wait_for_api()
        await self._create_projects()

        if not self.projects:
            logger.error("no_projects_created", hint="Check SECRET_TOKEN and API availability")
            return False

        logger.info("seeder_ready", project_count=len(self.projects))
        return True

    async def _wait_for_api(self, max_retries: int = 30):
        """Wait for API to become available."""
        for i in range(max_retries):
            try:
                resp = await self.client.get("/health")
                if resp.status_code == 200:
                    logger.info("api_ready", host=API_HOST)
                    return
            except httpx.ConnectError:
                pass
            logger.debug("waiting_for_api", attempt=i + 1, max_retries=max_retries)
            await asyncio.sleep(2)
        raise RuntimeError("API not available")

    async def _create_projects(self):
        """Create projects with different plans."""
        plans_to_create = [
            (Plan.FREE, "free_shop"),
            (Plan.PRO, "pro_store_1"),
            (Plan.PRO, "pro_store_2"),
            (Plan.ENTERPRISE, "enterprise_mall"),
        ]

        for plan, name_suffix in plans_to_create:
            project_name = f"seeder_{name_suffix}_{fake.random_int(1000, 9999)}"

            try:
                resp = await self.client.post(
                    "/api/v1/project",
                    json={"name": project_name, "plan": plan.value},
                    headers={"Authorization": f"Bearer {SECRET_TOKEN}"},
                )

                if resp.status_code == 200:
                    data = resp.json()
                    project = Project(
                        name=project_name,
                        plan=plan,
                        api_key=data["api_key"],
                    )
                    self.projects.append(project)
                    logger.info("project_created", name=project_name, plan=plan.value)
                else:
                    logger.error(
                        "project_create_failed",
                        name=project_name,
                        status=resp.status_code,
                        response=resp.text,
                    )

            except Exception as e:
                logger.error("project_create_error", error=str(e))

    async def run(self):
        """Run seeder with multiple simulated users."""
        logger.info("seeder_starting", users=NUM_USERS, speed_multiplier=SPEED_MULTIPLIER)

        tasks = [asyncio.create_task(self._run_user(i)) for i in range(NUM_USERS)]
        tasks.append(asyncio.create_task(self._report_stats()))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("seeder_stopped")

    async def _run_user(self, user_num: int):
        """Simulate a single user's behavior."""
        project = random.choice(self.projects)

        session = UserSession(
            user_id=f"user_{fake.uuid4()[:12]}",
            session_id=f"session_{fake.uuid4()[:16]}",
            project=project,
        )

        logger.info(
            "user_started", user_num=user_num, project=project.name, plan=project.plan.value
        )

        while self.running:
            try:
                await self._simulate_user_journey(session)

                # Between sessions: user might leave and come back
                if random.random() < 0.3:  # 30% chance to "leave"
                    await self._sleep(random.uniform(10, 30))
                    session.reset()
                    # 20% chance to switch to different project
                    if random.random() < 0.2:
                        session.project = random.choice(self.projects)

            except Exception as e:
                logger.error("user_error", user_num=user_num, error=str(e))
                self.stats["errors"] += 1
                await self._sleep(5)

    async def _simulate_user_journey(self, session: UserSession):
        """Simulate a realistic user journey."""
        num_pages = random.randint(1, 5)
        for _ in range(num_pages):
            await self._send_page_view(session)
            await self._sleep(random.uniform(2, 8))

        num_products = random.randint(1, 4)
        for _ in range(num_products):
            await self._send_product_view(session)
            await self._sleep(random.uniform(3, 10))

        for product in session.viewed_products[-3:]:
            if random.random() < 0.6:
                await self._send_add_to_cart(session, product)
                await self._sleep(random.uniform(1, 3))

        if session.cart and random.random() < 0.1:
            await self._send_remove_from_cart(session)
            await self._sleep(random.uniform(1, 2))

        if session.cart and random.random() < 0.15:
            await self._send_purchase(session)
            session.cart = []
            await self._sleep(random.uniform(2, 5))

        if random.random() < 0.2:
            await self._send_batch(session)

    async def _send_event(self, session: UserSession, event: dict[str, Any]):
        """Send single event to API."""
        try:
            resp = await self.client.post(
                "/api/v1/event",
                json=event,
                headers={"X-Api-Key": session.project.api_key},
            )

            if resp.status_code == 202:
                self.stats["events_sent"] += 1
            elif resp.status_code == 429:
                # Rate limited - slow down
                await self._sleep(5)
            else:
                self.stats["errors"] += 1

        except Exception:
            self.stats["errors"] += 1

    async def _send_batch(self, session: UserSession):
        """Send batch of events (simulates mobile SDK sync)."""
        batch_size = random.randint(3, 10)
        events = []

        for _ in range(batch_size):
            event_type = random.choices(
                [EventType.PAGE_VIEW, EventType.PRODUCT_VIEW, EventType.ADD_TO_CART],
                weights=[0.5, 0.35, 0.15],
            )[0]

            if event_type == EventType.PAGE_VIEW:
                events.append(self._make_page_view_event(session))
            elif event_type == EventType.PRODUCT_VIEW:
                events.append(self._make_product_view_event(session))
            else:
                product = random.choice(PRODUCT_CATALOG)
                events.append(self._make_add_to_cart_event(session, product))

        try:
            resp = await self.client.post(
                "/api/v1/event/batch",
                json={"events": events},
                headers={"X-Api-Key": session.project.api_key},
            )

            if resp.status_code == 202:
                self.stats["batches_sent"] += 1
                self.stats["events_sent"] += len(events)
            elif resp.status_code == 429:
                await self._sleep(5)
            else:
                self.stats["errors"] += 1

        except Exception:
            self.stats["errors"] += 1

    async def _send_page_view(self, session: UserSession):
        """Send PAGE_VIEW event."""
        event = self._make_page_view_event(session)
        await self._send_event(session, event)
        session.page_views += 1

    async def _send_product_view(self, session: UserSession):
        """Send PRODUCT_VIEW event."""
        event = self._make_product_view_event(session)
        await self._send_event(session, event)

    async def _send_add_to_cart(self, session: UserSession, product: dict):
        """Send ADD_TO_CART event."""
        event = self._make_add_to_cart_event(session, product)
        await self._send_event(session, event)
        session.cart.append(product)

    async def _send_remove_from_cart(self, session: UserSession):
        """Send REMOVE_FROM_CART event."""
        if not session.cart:
            return

        product = session.cart.pop(random.randint(0, len(session.cart) - 1))

        event = {
            "user_id": session.user_id,
            "session_id": session.session_id,
            "event_type": EventType.REMOVE_FROM_CART.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "properties": {
                "product_id": product["id"],
                "quantity": 1,
            },
        }
        await self._send_event(session, event)

    async def _send_purchase(self, session: UserSession):
        """Send PURCHASE event for all items in cart."""
        for product in session.cart:
            quantity = random.randint(1, 3)
            event = {
                "user_id": session.user_id,
                "session_id": session.session_id,
                "event_type": EventType.PURCHASE.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "properties": {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "category": product["category"],
                    "price": product["price"],
                    "quantity": quantity,
                    "currency": "USD",
                    "country": fake.country_code(),
                },
            }
            await self._send_event(session, event)
            await self._sleep(0.1)  # Small delay between items

    def _make_page_view_event(self, session: UserSession) -> dict[str, Any]:
        """Create PAGE_VIEW event."""
        return {
            "user_id": session.user_id,
            "session_id": session.session_id,
            "event_type": EventType.PAGE_VIEW.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "properties": {
                "page_url": f"https://shop.example.com{random.choice(PAGES)}",
                "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                "os": random.choice(["Windows", "macOS", "Linux", "iOS", "Android"]),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "country": fake.country_code(),
                "source": random.choice(["organic", "paid", "social", "email", "direct"]),
            },
        }

    def _make_product_view_event(self, session: UserSession) -> dict[str, Any]:
        """Create PRODUCT_VIEW event."""
        product = random.choice(PRODUCT_CATALOG)
        session.viewed_products.append(product)

        return {
            "user_id": session.user_id,
            "session_id": session.session_id,
            "event_type": EventType.PRODUCT_VIEW.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "properties": {
                "page_url": f"https://shop.example.com/products/{product['id']}",
                "product_id": product["id"],
                "product_name": product["name"],
                "category": product["category"],
                "price": product["price"],
                "currency": "USD",
                "browser": random.choice(["Chrome", "Firefox", "Safari"]),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
            },
        }

    def _make_add_to_cart_event(self, session: UserSession, product: dict) -> dict[str, Any]:
        """Create ADD_TO_CART event."""
        return {
            "user_id": session.user_id,
            "session_id": session.session_id,
            "event_type": EventType.ADD_TO_CART.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "properties": {
                "product_id": product["id"],
                "product_name": product["name"],
                "category": product["category"],
                "price": product["price"],
                "quantity": random.randint(1, 3),
                "currency": "USD",
            },
        }

    async def _sleep(self, seconds: float):
        """Sleep with speed multiplier applied."""
        await asyncio.sleep(seconds / SPEED_MULTIPLIER)

    async def _report_stats(self):
        """Periodically report statistics."""
        while self.running:
            await asyncio.sleep(30)
            logger.info(
                "seeder_stats",
                events_sent=self.stats["events_sent"],
                batches_sent=self.stats["batches_sent"],
                errors=self.stats["errors"],
            )

    async def shutdown(self):
        """Graceful shutdown."""
        self.running = False
        if self.client:
            await self.client.aclose()


async def main():
    seeder = EventSeeder()

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(seeder.shutdown()))

    if not await seeder.setup():
        return 1

    await seeder.run()
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("seeder_stopped_by_user")
        sys.exit(0)
