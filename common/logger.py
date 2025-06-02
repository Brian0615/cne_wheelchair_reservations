import inspect
import logging
import time
from functools import wraps


def initialize_logger(log_level: int = logging.DEBUG) -> logging.Logger:
    """Initialize and return a logger."""
    logger = logging.getLogger(inspect.stack()[1].frame.f_globals["__name__"])
    logger.setLevel(log_level)

    if not logger.hasHandlers():
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # Create a formatter and set it for handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s]: %(message)s')
        console_handler.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(console_handler)

    return logger


def timeit(logger: logging.Logger = None):
    """Decorator that reports the execution time using the provided logger or initializes one if not provided."""
    if logger is None:
        logger = initialize_logger()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            logger.info("Function %r executed in %.4f seconds", func.__name__, elapsed_time)
            return result
        return wrapper
    return decorator
