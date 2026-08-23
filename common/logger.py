import contextvars
import inspect
import json
import logging
import os
import time
import traceback
from functools import wraps
from inspect import iscoroutinefunction
from typing import Optional

# Correlation identifiers propagated via contextvars so any logger anywhere in the call stack
# automatically includes them, without threading them through every function signature.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
username_var: contextvars.ContextVar[str] = contextvars.ContextVar("username", default="-")

_RESERVED_LOG_RECORD_ATTRS = frozenset(vars(logging.makeLogRecord({})).keys())


# pylint: disable=too-few-public-methods
class ContextFilter(logging.Filter):
    """Injects the current request_id and username contextvars into every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.username = username_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON, suitable for CloudWatch Logs Insights."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%f%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "username": getattr(record, "username", "-"),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS and key not in ("request_id", "username"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))
        return json.dumps(payload, default=str)


def _resolve_log_level(default: int = logging.DEBUG) -> int:
    """Resolve the log level from the LOG_LEVEL env var, falling back to `default`."""
    level_name = os.getenv("LOG_LEVEL")
    if not level_name:
        return default
    return logging.getLevelNamesMapping().get(level_name.upper(), default)


def initialize_logger(log_level: Optional[int] = None) -> logging.Logger:
    """Initialize and return a logger."""
    logger = logging.getLogger(inspect.stack()[1].frame.f_globals["__name__"])
    logger.setLevel(log_level if log_level is not None else _resolve_log_level())

    if not logger.hasHandlers():
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logger.level)
        console_handler.setFormatter(JsonFormatter())
        console_handler.addFilter(ContextFilter())

        # Add the handlers to the logger
        logger.addHandler(console_handler)

    return logger


def timeit(logger: Optional[logging.Logger] = None):
    """Decorator that reports the execution time using the provided logger or initializes one if not
    provided. Supports both sync and async functions."""

    def decorator(func):
        _logger = logger or initialize_logger()

        def _log_duration(elapsed_time: float):
            _logger.info(
                "Function executed",
                extra={"function": func.__name__, "duration_ms": round(elapsed_time * 1000, 2)},
            )

        if iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                result = await func(*args, **kwargs)
                _log_duration(time.perf_counter() - start_time)
                return result

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            _log_duration(time.perf_counter() - start_time)
            return result

        return sync_wrapper

    return decorator
