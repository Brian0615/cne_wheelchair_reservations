import asyncio
import logging
import time
import unittest
from unittest.mock import patch

from common.logger import ContextFilter, PlainFormatter, initialize_logger, timeit, username_var


def _make_record(message: str = "hello", level: int = logging.INFO, **extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test.logger",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=None,
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


# pylint: disable=no-member
class TestContextFilter(unittest.TestCase):
    """Test the ContextFilter class."""

    def tearDown(self):
        username_var.set("-")

    def test_defaults_when_unset(self):
        """Test that username defaults to '-' when unset."""
        record = _make_record()
        ContextFilter().filter(record)
        self.assertEqual("-", record.username)

    def test_injects_context_values(self):
        """Test that username is injected from the contextvar."""
        username_var.set("brian")
        record = _make_record()
        ContextFilter().filter(record)
        self.assertEqual("brian", record.username)

    def test_does_not_override_explicit_username(self):
        """A username passed explicitly via `extra` (e.g. during login, before the
        contextvar is set) must not be clobbered by the contextvar's default."""
        record = _make_record(username="explicit_user")
        ContextFilter().filter(record)
        self.assertEqual("explicit_user", record.username)


class TestPlainFormatter(unittest.TestCase):
    """Test the PlainFormatter class."""

    def test_format_includes_expected_fields(self):
        """Test that formatting produces a readable line with the expected fields."""
        record = _make_record(message="Something happened", username="brian")
        line = PlainFormatter().format(record)
        self.assertIn("INFO", line)
        self.assertIn("test.logger", line)
        self.assertIn("Something happened", line)
        self.assertIn("brian", line)

    def test_format_includes_extra_fields(self):
        """Test that ad-hoc `extra` fields are appended as key=value pairs."""
        record = _make_record(username="-", duration_ms=12.34, rental_id="W0820001")
        line = PlainFormatter().format(record)
        self.assertIn("duration_ms=12.34", line)
        self.assertIn("rental_id=W0820001", line)

    def test_format_includes_exception(self):
        """Test that exception info is appended to the line."""
        try:
            raise ValueError("boom")
        except ValueError:
            record = _make_record(username="-")
            record.exc_info = __import__("sys").exc_info()
        line = PlainFormatter().format(record)
        self.assertIn("ValueError: boom", line)


class TestInitializeLogger(unittest.TestCase):
    """Test the initialize_logger function."""

    def test_default_level_is_debug(self):
        """Test that the default level is DEBUG when LOG_LEVEL is unset."""
        with patch.dict("os.environ", {}, clear=True):
            logger = initialize_logger()
            self.assertEqual(logging.DEBUG, logger.level)

    def test_log_level_env_var_is_respected(self):
        """Test that the LOG_LEVEL env var overrides the default level."""
        with patch.dict("os.environ", {"LOG_LEVEL": "WARNING"}):
            logger = initialize_logger()
            self.assertEqual(logging.WARNING, logger.level)

    def test_explicit_level_overrides_env_var(self):
        """Test that an explicitly passed level takes precedence over LOG_LEVEL."""
        with patch.dict("os.environ", {"LOG_LEVEL": "WARNING"}):
            logger = initialize_logger(log_level=logging.ERROR)
            self.assertEqual(logging.ERROR, logger.level)


class TestTimeit(unittest.TestCase):
    """Test the timeit decorator."""

    def test_sync_function_logs_duration(self):
        """Test that a sync function's duration is logged via `extra`."""
        logger = logging.getLogger("test.timeit.sync")
        with patch.object(logger, "info") as mock_info:

            @timeit(logger=logger)
            def slow():
                time.sleep(0.05)
                return "done"

            result = slow()
            self.assertEqual("done", result)
            mock_info.assert_called_once()
            _, kwargs = mock_info.call_args
            self.assertGreaterEqual(kwargs["extra"]["duration_ms"], 40)
            self.assertEqual("slow", kwargs["extra"]["function"])

    def test_async_function_logs_correct_duration(self):
        """Test that an async function is actually awaited and timed correctly."""
        logger = logging.getLogger("test.timeit.async")
        with patch.object(logger, "info") as mock_info:

            @timeit(logger=logger)
            async def slow_async():
                await asyncio.sleep(0.05)
                return "done"

            result = asyncio.run(slow_async())
            self.assertEqual("done", result)
            mock_info.assert_called_once()
            _, kwargs = mock_info.call_args
            self.assertGreaterEqual(kwargs["extra"]["duration_ms"], 40)
            self.assertEqual("slow_async", kwargs["extra"]["function"])


if __name__ == "__main__":
    unittest.main()
