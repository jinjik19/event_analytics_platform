import pytest
from uuid import UUID
from datetime import datetime, UTC

from domain.event.models import Event, Properties
from domain.event.types import EventType
from domain.utils.generate_uuid import generate_uuid
from infrastructure.stream.redis_consumer import RedisEventConsumer
from infrastructure.stream.redis_producer import RedisEventProducer


@pytest.fixture
def sample_event():
    return Event.create(
        project_id=generate_uuid(),
        user_id="test_user",
        session_id="test_session",
        event_type=EventType.PAGE_VIEW,
        timestamp=datetime.now(UTC),
        properties=Properties(
            page_url="http://example.com",
            price=100,
            quantity=2
        )
    )


async def test_consume_event_success(fake_stream_redis, sample_event, mock_logger):
    stream_name = "test_events"
    group_name = "test_group"
    consumer_name = "test_worker"
    # Setup producer and consumer
    producer = RedisEventProducer(fake_stream_redis, stream_name=stream_name)
    consumer = RedisEventConsumer(
        redis=fake_stream_redis,
        logger=mock_logger,
        group_name=group_name,
        consumer_name=consumer_name,
        stream_name=stream_name,
    )

    # Create consumer group
    await consumer.ensure_group()
    # Publish an event
    await producer.publish(sample_event)
    # Read batch with count=1 to get the single published event
    consumed_batch = await consumer.read_batch(count=1)

    assert len(consumed_batch) == 1
    consumed = consumed_batch[0]

    # Check that the consumed event matches the published event
    assert isinstance(consumed.msg_id, str)
    assert consumed.event.event_id == sample_event.event_id
    assert consumed.event.user_id == "test_user"
    assert consumed.event.properties.price == 100

    # Check types after deserialization
    assert isinstance(consumed.event.timestamp, datetime)
    assert isinstance(consumed.event.event_id, UUID)

    await consumer.ack([consumed.msg_id])

    # Check Pending list is empty after ack
    pending_info = await fake_stream_redis.xpending(stream_name, group_name)
    assert pending_info['pending'] == 0


@pytest.mark.asyncio
async def test_ensure_group_idempotency(fake_stream_redis, mock_logger):
    consumer = RedisEventConsumer(fake_stream_redis, mock_logger, "group1", "worker1", "s1")
    # Create group for the first time
    await consumer.ensure_group()
    # Ignore exception BUSYGROUP
    await consumer.ensure_group()

    # Check that the group exists and only one group is created
    groups = await fake_stream_redis.xinfo_groups("s1")
    assert len(groups) == 1
    assert groups[0]['name'] == b"group1"
