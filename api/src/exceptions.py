class DeviceNotFoundException(Exception):
    """Exception raised when a device is not found in the inventory."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ReservationNotFoundOrNotEditableException(Exception):
    """Exception raised when a device is not found in the inventory."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class UniqueViolation(ValueError):
    """Exception raised when a unique constraint is violated."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
