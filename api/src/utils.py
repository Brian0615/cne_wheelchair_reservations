from functools import wraps

from fastapi import HTTPException

from api.src.exceptions import DeviceNotFoundException, ReservationNotFoundOrNotEditableException, \
    DeviceNotFoundOrInvalidStatusException, RentalNotFoundOrNotEditableException, \
    NewReservationNotFoundOrNotEditableException
from common.logger import initialize_logger

logger = initialize_logger()


def auto_process_database_errors(func):
    """Automatically process database errors and raise appropriate HTTPExceptions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Wrap the function and process database errors."""
        try:
            return func(*args, **kwargs)
        except DeviceNotFoundException as exc:
            logger.warning("Device not found", extra={"detail": exc.message})
            raise HTTPException(status_code=404, detail=exc.message) from exc
        except (
                DeviceNotFoundOrInvalidStatusException,
                RentalNotFoundOrNotEditableException,
                ReservationNotFoundOrNotEditableException,
                NewReservationNotFoundOrNotEditableException,
        ) as exc:
            logger.warning(
                "Invalid request rejected",
                extra={"detail": exc.message, "exception_type": type(exc).__name__},
            )
            raise HTTPException(status_code=400, detail=exc.message) from exc

    return wrapper
