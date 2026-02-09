import signal

from application.worker.graceful_killer import GracefulKiller

async def test_graceful_killer_signal_handler():
    killer = GracefulKiller()

    assert not killer.shutdown_event.is_set()

    killer.signal_handler(signal.SIGTERM, None)

    assert killer.shutdown_event.is_set()
