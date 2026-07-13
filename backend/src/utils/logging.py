"""
ASEP — Structured Logging Configuration
==========================================
Configures structlog for JSON-formatted, level-filtered logging
that works identically in local dev (pretty) and production (JSON).

TODO (Phase 0.2):
    - Add OpenTelemetry trace/span context injection
    - Add log shipping to Loki / CloudWatch / GCS
    - Add request-id propagation through async context vars
"""

from __future__ import annotations

import logging
import sys
from typing import Literal

import structlog


def configure_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    json_logs: bool = False,
) -> None:
    """
    Configure the global logging stack.

    In development (json_logs=False), logs are pretty-printed with colours.
    In production (json_logs=True), logs are emitted as JSON lines.

    Args:
        level:      Minimum log level string (e.g. "INFO").
        json_logs:  Emit JSON instead of human-readable output.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Standard library root logger
    logging.basicConfig(
        level=log_level,
        stream=sys.stdout,
        format="%(message)s",
    )

    # Shared processors
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Apply renderer to stdlib formatter
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a structured logger for the given module name.

    Usage:
        logger = get_logger(__name__)
        logger.info("something happened", key="value")

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A bound structlog logger instance.
    """
    return structlog.get_logger(name)
