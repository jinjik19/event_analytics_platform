import asyncio
from unittest.mock import ANY, AsyncMock, MagicMock, patch
import pytest

from application.worker.loop import WorkerLoop

@pytest.fixture
def mock_processor():
    processor = AsyncMock()
    processor.ensure_startup = AsyncMock()
    processor.process = AsyncMock()
    return processor


@pytest.fixture
def mock_killer():
    killer = MagicMock()
    killer.shutdown_event.is_set = MagicMock()
    return killer


@pytest.fixture
def worker_loop(mock_processor, mock_killer, mock_logger):
    return WorkerLoop(
        processor=mock_processor,
        killer=mock_killer,
        logger=mock_logger
    )


async def test_loop_normal_execution(worker_loop, mock_processor, mock_killer):
    mock_killer.shutdown_event.is_set.side_effect = [False, True]

    await worker_loop.run()

    mock_processor.ensure_startup.assert_called_once()
    mock_processor.process.assert_called_once()


async def test_loop_handles_exception(worker_loop, mock_processor, mock_killer, mock_logger):
    mock_killer.shutdown_event.is_set.side_effect = [False, True]
    mock_processor.process.side_effect = ValueError("Redis died")

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await worker_loop.run()
        mock_sleep.assert_called_once_with(5)

    mock_logger.error.assert_called_once()
    assert "worker_unexpected_error" in mock_logger.error.call_args[0]

@pytest.mark.asyncio
async def test_loop_handles_cancellation(worker_loop, mock_processor, mock_killer, mock_logger):
    mock_killer.shutdown_event.is_set.side_effect = [False]
    mock_processor.process.side_effect = asyncio.CancelledError()

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await worker_loop.run()
        mock_sleep.assert_not_called()

    mock_logger.error.assert_any_call("worker_task_cancelled", error=ANY)
