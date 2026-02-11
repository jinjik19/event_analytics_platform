import asyncpg
from redis.exceptions import ConnectionError, TimeoutError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


db_retry_policy = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(
        (
            ConnectionError,
            TimeoutError,
            asyncpg.CannotConnectNowError,
            asyncpg.ConnectionDoesNotExistError,
        )
    ),
    reraise=True,
)
