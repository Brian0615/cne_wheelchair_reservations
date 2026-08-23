import contextvars
import inspect
import logging
import os
import time
from functools import wraps
from inspect import iscoroutinefunction
from typing import Optional

# The current user, propagated via a contextvar so any logger anywhere in the call stack
# automatically includes it, without threading it through every function signature.
username_var: contextvars.ContextVar[str] = contextvars.ContextVar("username", default="-")

_RESERVED_LOG_RECORD_ATTRS = frozenset(vars(logging.makeLogRecord({})).keys())


# pylint: disable=too-few-public-methods
class ContextFilter(logging.Filter):
    """Injects the current username contextvar into every LogRecord, unless the log call
    already passed an explicit `username` via `extra` (e.g. before the contextvar is set)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "username"):
            record.username = username_var.get()
        return True


class PlainFormatter(logging.Formatter):
    """Formats log records as a single human-readable line, with any `extra` fields
    appended as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        line = (
            f"{self.formatTime(record, '%Y-%m-%d %H:%M:%S')} "
            f"{record.levelname} {record.name} [{getattr(record, 'username', '-')}]: "
            f"{record.getMessage()}"
        )
        extras = {
            key: value for key, value in record.__dict__.items()
            if key not in _RESERVED_LOG_RECORD_ATTRS and key != "username"
        }
        if extras:
            line += " " + " ".join(f"{key}={value}" for key, value in extras.items())
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


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
        console_handler.setFormatter(PlainFormatter())
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
