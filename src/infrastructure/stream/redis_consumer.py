from typing import Any, cast

import msgpack  # type: ignore[import-untyped]
from redis.exceptions import ResponseError
from structlog import BoundLogger

from domain.event.consumer import ConsumedEvent
from infrastructure.di.providers.types import StreamRedis
from infrastructure.stream.mapper import dict_to_event


class RedisEventConsumer:
    def __init__(
        self,
        redis: StreamRedis,
        logger: BoundLogger,
        group_name: str,
        consumer_name: str,
        stream_name: str = "events_stream",
    ) -> None:
        self._redis = redis
        self._group_name = group_name
        self._consumer_name = consumer_name
        self._stream_name = stream_name

        self._logger = logger.bind(
            component="redis_event_consumer",
            group=group_name,
            consumer=consumer_name,
        )

    async def ensure_group(self) -> None:
        try:
            # '0' mean "read from the beginning of the stream".
            # mkstream=True creates the stream if it doesn't exist
            await self._redis.xgroup_create(
                name=self._stream_name, groupname=self._group_name, id="0", mkstream=True
            )
            self._logger.info(f"Consumer group '{self._group_name}' created.")
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                self._logger.debug(f"Consumer group '{self._group_name}' already exists.")
            else:
                raise e

    async def read_batch(self, count: int = 100, block_ms: int = 1000) -> list[ConsumedEvent]:
        raw_messages = await self._fetch_messages(count=count, block_ms=block_ms)

        if not raw_messages:
            return []

        result = []
        for msg_id_bytes, fields in raw_messages:
            consumed_events = self._process_message(msg_id_bytes, fields)
            if consumed_events:
                result.append(consumed_events)

        return result

    async def ack(self, msg_ids: list[str]) -> None:
        if not msg_ids:
            return
        await self._redis.xack(self._stream_name, self._group_name, *msg_ids)  # type: ignore[no-untyped-call]
        self._logger.debug("events_acked", count=len(msg_ids))

    async def _fetch_messages(self, count: int, block_ms: int) -> list[Any]:
        # XREADGROUP return nested structure
        response = await self._redis.xreadgroup(
            groupname=self._group_name,
            consumername=self._consumer_name,
            streams={self._stream_name: ">"},
            count=count,
            block=block_ms,
        )

        if not response:
            return []

        return cast(list[Any], response[0][1])

    def _process_message(
        self, msg_id_bytes: bytes, fields: dict[bytes, bytes]
    ) -> ConsumedEvent | None:
        msg_id = msg_id_bytes.decode("utf-8") if isinstance(msg_id_bytes, bytes) else msg_id_bytes

        raw_data = fields.get(b"data")
        if not raw_data:
            self._logger.warning("empty_message_data", msg_id=msg_id)
            return None

        try:
            data_dict = msgpack.unpackb(raw_data, raw=False)
            event = dict_to_event(data_dict)
            return ConsumedEvent(msg_id=msg_id, event=event)
        except Exception as e:
            # Log and skip malformed message
            # But in future needs to send it to dead-letter queue
            self._logger.error("malformed_message", msg_id=msg_id, error=str(e))
            return None
