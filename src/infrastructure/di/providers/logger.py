from typing import cast

import structlog
from dishka import Provider, Scope, provide
from structlog import BoundLogger


class LoggerProvider(Provider):
    @provide(scope=Scope.APP)
    def get_logger(self) -> BoundLogger:
        return cast(BoundLogger, structlog.get_logger("event_analytics_api"))
