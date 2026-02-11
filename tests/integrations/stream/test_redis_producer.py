import pytest
import msgpack
from uuid import UUID
from datetime import datetime, UTC

from domain.event.models import Event, Properties
from domain.event.types import EventType
from domain.utils.generate_uuid import generate_uuid
from infrastructure.stream.redis_producer import RedisEventProducer

@pytest.fixture
def sample_event():
    return Event.create(
        project_id=generate_uuid(),
        user_id="u1",
        session_id="s1",
        event_type=EventType.PAGE_VIEW,
        timestamp=datetime.now(UTC),
        properties=Properties(page_url="http://test.com")
    )


async def test_publish_single_event(fake_stream_redis, sample_event):
    producer = RedisEventProducer(redis=fake_stream_redis, stream_name="test_stream")

    await producer.publish(sample_event)

    streams = await fake_stream_redis.xread({"test_stream": "0-0"}, count=1)

    assert len(streams) == 1
    stream_name, messages = streams[0]
    assert stream_name == b"test_stream"

    _, fields = messages[0]
    raw_data = fields[b"data"]

    decoded_dict = msgpack.unpackb(raw_data)
    assert decoded_dict["user_id"] == "u1"
    assert decoded_dict["event_id"] == str(sample_event.event_id)
    assert decoded_dict["properties"]["page_url"] == "http://test.com"


@pytest.mark.asyncio
async def test_publish_batch_events(fake_stream_redis, sample_event):
    producer = RedisEventProducer(redis=fake_stream_redis, stream_name="test_stream")
    events = [sample_event, sample_event, sample_event]

    await producer.publish_batch(events)

    count = await fake_stream_redis.xlen("test_stream")
    assert count == 3
