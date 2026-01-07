import logging
import sys

import structlog
from structlog.types import Processor

from infrastructure.config.settings import settings


def configure_logger() -> None:
    """Configure the structlog logger."""
    formatter = configure_structlogger()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def configure_structlogger() -> structlog.stdlib.ProcessorFormatter:
    """Configure structlog for the application."""
    shared_processors: list[Processor] = create_shared_configuration()

    # Choose renderer based on environment
    renderer_processor: Processor
    if settings.is_prod:
        # Render logs as JSON
        renderer_processor = structlog.processors.JSONRenderer()
    else:
        renderer_processor = structlog.dev.ConsoleRenderer()

    # Configure structlog
    structlog.configure(
        processors=[*shared_processors, renderer_processor],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(settings.log_level),
        cache_logger_on_first_use=True,
    )

    # Redirect standard logging to structlog
    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer_processor,
        ],
    )


def create_shared_configuration() -> list[Processor]:
    """Create shared structlog configuration processors."""
    return [
        # Merge context variables (request ID, user ID, etc.)
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),  # Add ISO 8601 timestamp to log entries
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            },
        ),
        structlog.processors.format_exc_info,  # Tracebacks -> text
    ]
