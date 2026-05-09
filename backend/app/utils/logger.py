"""Structured logging configuration."""

from __future__ import annotations

import logging
from typing import Any

import structlog


def configure_logging() -> None:
	"""Configure structlog for JSON output."""
	logging.basicConfig(level=logging.INFO, format="%(message)s")
	structlog.configure(
		processors=[
			structlog.processors.TimeStamper(fmt="iso"),
			structlog.processors.add_log_level,
			structlog.processors.StackInfoRenderer(),
			structlog.processors.format_exc_info,
			structlog.processors.JSONRenderer(),
		],
		context_class=dict,
		logger_factory=structlog.stdlib.LoggerFactory(),
		wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
		cache_logger_on_first_use=True,
	)


def get_logger() -> structlog.stdlib.BoundLogger:
	"""Return a structlog logger instance."""
	return structlog.get_logger()


def bind_logger_context(logger: structlog.stdlib.BoundLogger, **kwargs: Any) -> structlog.stdlib.BoundLogger:
	"""Bind context key-values to the logger."""
	return logger.bind(**kwargs)
