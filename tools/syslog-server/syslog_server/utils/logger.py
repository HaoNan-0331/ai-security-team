"""
Logging configuration for Syslog Server.

Uses structlog for structured logging with JSON output in production.
"""

import logging
import sys

import structlog
from structlog.types import Processor

from syslog_server.config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Configure structlog
    processors: list[Processor] = [
        # Add context variables
        structlog.contextvars.merge_contextvars,
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add call site info (file, line, function)
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        # Handle exceptions
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Choose output format based on environment
    if settings.log_level == "DEBUG":
        # Development: pretty console output
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )
    else:
        # Production: JSON output
        processors.extend(
            [
                structlog.processors.JSONRenderer(),
            ]
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def configure_logging() -> None:
    """Configure logging (called on import)."""
    setup_logging()


def get_logger(name: str | None = None):
    """Get a structlog logger instance."""
    return structlog.get_logger(name)
