from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from redis.asyncio import from_url
from structlog import BoundLogger

from domain.event.consumer import EventConsumer
from domain.event.producer import EventProducer
from infrastructure.config.settings import Settings
from infrastructure.di.providers.types import StreamRedis
from infrastructure.stream.redis_consumer import RedisEventConsumer
from infrastructure.stream.redis_producer import RedisEventProducer


class StreamProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_client(self, settings: Settings) -> AsyncIterable[StreamRedis]:
        client = from_url(
            url=settings.stream_url,
            encoding="utf-8",
            decode_responses=False,
        )

        yield StreamRedis(client)
        await client.aclose()  # type: ignore[attr-defined]

    @provide
    def get_producer(self, client: StreamRedis) -> EventProducer:
        return RedisEventProducer(client)

    @provide(scope=Scope.REQUEST)
    def get_consumer(self, client: StreamRedis, logger: BoundLogger) -> EventConsumer:
        import socket

        worker_name = socket.gethostname()

        return RedisEventConsumer(
            redis=client,
            logger=logger,
            group_name="main_group",
            consumer_name=worker_name,
        )
