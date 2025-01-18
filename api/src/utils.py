from functools import wraps

from fastapi import HTTPException
from psycopg.errors import DatabaseError, UniqueViolation


def auto_process_database_errors(func):
    """Automatically process database errors and raise appropriate HTTPExceptions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrap the function and process database errors."""
        try:
            return func(*args, **kwargs)
        except UniqueViolation as exc:
            raise HTTPException(
                status_code=409,
                detail=f"{exc.diag.message_primary} - {exc.diag.message_detail}",
            ) from exc
        except DatabaseError as exc:
            match exc.sqlstate:
                case "E1001" | "E2001":
                    raise HTTPException(
                        status_code=404,
                        detail=exc.diag.message_primary,
                    ) from exc
                case "E1002":
                    raise HTTPException(
                        status_code=409,
                        detail=exc.diag.message_primary,
                    ) from exc
                case _:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Database Error ({exc.sqlstate}): {exc.diag.message_primary}",
                    ) from exc

    return wrapper
