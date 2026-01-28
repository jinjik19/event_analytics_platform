import os
import random

import structlog
from locust import HttpUser, events
from locust.runners import WorkerRunner

from tests.load.data_generator import setup_projects


logger = structlog.get_logger("load_test")
_raw_keys = os.getenv("LOAD_TEST_API_KEYS", "")
API_KEYS: list[str] = [k.strip() for k in _raw_keys.split(",") if k.strip()]


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """
    Register message listeners for distributed execution.
    """
    if isinstance(environment.runner, WorkerRunner):
        environment.runner.register_message("api_keys_update", on_keys_received)


def on_keys_received(environment, msg, **kwargs):
    """Worker receives keys from Master."""
    global API_KEYS
    API_KEYS.extend(msg.data)
    logger.info("worker_received_keys", count=len(msg.data))


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Executes ONLY on Master (or local).
    Creates projects and distributes keys to workers.
    """
    if not isinstance(environment.runner, WorkerRunner):
        logger.info("master_starting_setup")
        global API_KEYS
        if API_KEYS:
            logger.info("using_env_api_keys", count=len(API_KEYS))
            keys = API_KEYS # Используем то, что есть
        else:
            logger.info("master_starting_setup")
            keys = setup_projects(environment.host)
            API_KEYS.extend(keys)

        if environment.runner:
            environment.runner.send_message("api_keys_update", keys)


class AnalyticsBaseUser(HttpUser):
    """Base class handling common logic and metrics."""
    abstract = True

    def on_start(self):
        import time
        timeout = 10
        while not API_KEYS and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if not API_KEYS:
            logger.error("no_api_keys_available_stopping")
            self.environment.runner.quit()
            return

    def post_event(self, url: str, payload: dict, name: str, expected_status=202):
        current_api_key = random.choice(API_KEYS)

        headers = {
            "X-Api-Key": current_api_key,
            "Content-Type": "application/json",
        }

        with self.client.post(
            url,
            json=payload,
            headers=headers,
            catch_response=True,
            name=name,
        ) as response:
            if response.status_code == expected_status:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limit exceeded")
            elif response.status_code == 401:
                logger.error("auth_fail", key=self.api_key[:10])
                response.failure("Auth failed")
            else:
                response.failure(f"Unexpected {response.status_code}: {response.text[:100]}")
