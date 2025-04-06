from functools import wraps

from fastapi import HTTPException

from api.src.exceptions import DeviceNotFoundException


def auto_process_database_errors(func):
    """Automatically process database errors and raise appropriate HTTPExceptions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrap the function and process database errors."""
        try:
            return func(*args, **kwargs)
        except DeviceNotFoundException as exc:
            raise HTTPException(status_code=404, detail=exc.message) from exc

    return wrapper
