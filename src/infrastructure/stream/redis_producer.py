import dataclasses
from datetime import datetime
from typing import Any
from uuid import UUID

import msgpack  # type: ignore[import-untyped]

from domain.event.models import Event
from infrastructure.di.providers.types import StreamRedis


def msgpack_encoder(obj: Any) -> Any:  # noqa: ANN401
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


class RedisEventProducer:
    def __init__(
        self, redis: StreamRedis, stream_name: str = "events_stream", max_len: int = 100_000
    ) -> None:
        self._redis = redis
        self._stream_name = stream_name
        self._max_len = max_len

    async def publish(self, event: Event) -> None:
        event_dict = dataclasses.asdict(event)
        payload = msgpack.packb(event_dict, default=msgpack_encoder, use_bin_type=True)

        await self._redis.xadd(
            name=self._stream_name,
            fields={"data": payload},
            maxlen=self._max_len,
            approximate=True,
        )

    async def publish_batch(self, events: list[Event]) -> None:
        async with self._redis.pipeline() as pipe:
            for event in events:
                event_dict = dataclasses.asdict(event)
                payload = msgpack.packb(event_dict, default=msgpack_encoder, use_bin_type=True)

                pipe.xadd(
                    name=self._stream_name,
                    fields={"data": payload},
                    maxlen=self._max_len,
                    approximate=True,
                )

            await pipe.execute()
