import os

import pytz


def get_default_timezone():
    """Get the default timezone"""
    return pytz.timezone(os.getenv("DEFAULT_TIMEZONE", "America/Toronto"))
