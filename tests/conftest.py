"""Pytest configuration for the test suite.

Sets required environment variables and suppresses Streamlit's benign
"missing ScriptRunContext" warning using both logging configuration and
a filter on sys.stderr.
"""
import logging
import os
import sys

from datetime import datetime


class _ScriptRunContextSuppressor:
    """Wrapper for stderr that filters out the ScriptRunContext warning."""

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = ""

    def write(self, text):
        if "missing ScriptRunContext" not in text and "No runtime found" not in text:
            self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()

    def isatty(self):
        return self.original_stderr.isatty() if hasattr(self.original_stderr, "isatty") else False

    def __getattr__(self, name):
        return getattr(self.original_stderr, name)


class _SuppressScriptRunContextFilter(logging.Filter):
    """Filter out log records containing benign Streamlit warnings."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        if "missing ScriptRunContext" in msg or "No runtime found" in msg:
            return False
        return True


def pytest_configure(config):
    """Configure pytest with required env vars and suppress the ScriptRunContext warning."""
    os.environ.setdefault("API_HOST", "localhost")
    os.environ.setdefault("API_PORT", "8595")
    os.environ.setdefault("AUTH_METHOD", "local")
    os.environ.setdefault("AUTH_CONFIG_PATH", "/tmp/auth_config.yaml")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    os.environ.setdefault("PDF_PASSWORD", "test")
    os.environ.setdefault("S3_BUCKET", "test-bucket")
    os.environ.setdefault("CNE_YEAR", str(datetime.now().year))

    for logger_name in [
        "streamlit",
        "streamlit.runtime",
        "streamlit.runtime.caching",
        "streamlit.runtime.caching.cache_data_api",
        "streamlit.runtime.scriptrunner",
        "streamlit.runtime.scriptrunner_utils.script_run_context",
    ]:
        logging.getLogger(logger_name).addFilter(_SuppressScriptRunContextFilter())

    sys.stderr = _ScriptRunContextSuppressor(sys.stderr)
