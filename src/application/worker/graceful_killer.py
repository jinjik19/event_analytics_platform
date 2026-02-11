import asyncio


class GracefulKiller:
    def __init__(self) -> None:
        self.shutdown_event = asyncio.Event()

    def signal_handler(self, signum: int, frame: object) -> None:
        self.shutdown_event.set()
