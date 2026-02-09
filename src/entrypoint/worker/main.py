import asyncio
import signal

from dishka import make_async_container
from structlog import get_logger

from application.worker.graceful_killer import GracefulKiller
from application.worker.loop import WorkerLoop
from infrastructure.di.providers.db import DbProvider
from infrastructure.di.providers.logger import LoggerProvider
from infrastructure.di.providers.settings import SettingsProvider
from infrastructure.di.providers.stream import StreamProvider
from infrastructure.di.providers.worker import WorkerProvider


logger = get_logger()


async def main() -> None:
    container = make_async_container(
        SettingsProvider(),
        LoggerProvider(),
        StreamProvider(),
        WorkerProvider(),
        DbProvider(),
    )

    try:
        async with container() as scope:
            killer = await scope.get(GracefulKiller)
            worker = await scope.get(WorkerLoop)

            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, killer.signal_handler, sig, None)

            await worker.run()
    except Exception as e:
        logger.critical("worker_crashed_at_startup", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
