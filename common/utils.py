import os
from pathlib import Path

import pytz


def get_default_timezone():
    """Get the default timezone"""
    return pytz.timezone(os.getenv("DEFAULT_TIMEZONE", "America/Toronto"))


def read_secret(secret_or_secret_path: str):
    """Read secret (if given value is a filepath, read that file; otherwise, use value as secret)"""
    try:
        # value is path to secret
        return Path(secret_or_secret_path).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        # value is secret itself, not path to secret
        return secret_or_secret_path
