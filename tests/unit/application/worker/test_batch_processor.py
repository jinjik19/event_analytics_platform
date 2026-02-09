from unittest.mock import AsyncMock, MagicMock
import pytest

from application.worker.batch_processor import BatchProcessor

@pytest.fixture
def mock_consumer():
    consumer = AsyncMock()
    consumer.read_batch = AsyncMock()
    consumer.ack = AsyncMock()
    consumer.ensure_group = AsyncMock()
    return consumer


@pytest.fixture
def processor(mock_consumer, mock_logger, mock_settings):
    return BatchProcessor(
        consumer=mock_consumer,
        logger=mock_logger,
        settings=mock_settings
    )


async def test_ensure_startup_calls_consumer(processor, mock_consumer):
    await processor.ensure_startup()
    mock_consumer.ensure_group.assert_called_once()


async def test_process_empty_batch(processor, mock_consumer):
    mock_consumer.read_batch.return_value = []

    await processor.process()

    mock_consumer.read_batch.assert_called_once_with(count=10, block_ms=1000)
    mock_consumer.ack.assert_not_called()


async def test_process_batch_success(processor, mock_consumer):
    event1 = MagicMock(msg_id="1")
    event2 = MagicMock(msg_id="2")
    mock_consumer.read_batch.return_value = [event1, event2]

    await processor.process()

    mock_consumer.ack.assert_called_once_with(["1", "2"])
