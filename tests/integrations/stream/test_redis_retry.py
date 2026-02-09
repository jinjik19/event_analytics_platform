import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from redis.exceptions import ConnectionError

from infrastructure.stream.redis_producer import RedisEventProducer
from infrastructure.di.providers.types import StreamRedis

@pytest.mark.asyncio
async def test_producer_retries_on_connection_error(make_event):
    mock_redis = MagicMock(spec=StreamRedis)
    mock_redis.xadd = AsyncMock()
    mock_redis.xadd.side_effect = [ConnectionError("Network blink"), "msg-id-123"]

    producer = RedisEventProducer(mock_redis)

    with patch("tenacity.nap.time.sleep", MagicMock()):
         dummy_event = make_event()

         await producer.publish(dummy_event)

    assert mock_redis.xadd.call_count == 2
