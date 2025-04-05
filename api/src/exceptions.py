class DeviceNotFoundException(Exception):
    """Exception raised when a device is not found in the inventory."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NewDeviceNotFoundException(Exception):
    """Exception raised when a device is not found in the inventory."""

    def __init__(self, cne_year: int, device_id: str):
        self.message = f"Device {device_id} (cne_year={cne_year}) not found in the inventory"
        super().__init__(self.message)


class RentalNotFoundOrNotEditableException(Exception):
    """Exception raised when a rental is not found in the inventory or cannot be edited"""

    def __init__(self, cne_year: int, rental_id: str):
        self.message = f"Rental {rental_id} (cne_year={cne_year}) not found or cannot be edited"
        super().__init__(self.message)


class ReservationNotFoundOrNotEditableException(Exception):
    """Exception raised when a reservation is not found in the inventory."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NewReservationNotFoundOrNotEditableException(Exception):
    """Exception raised when a reservation is not found in the inventory."""
    def __init__(self, cne_year: int, reservation_id: str):
        self.message = (
            f"Reservation {reservation_id} (cne_year={cne_year}) not found or "
            f"is un-editable (because it is cancelled/completed/picked up)"
        )
        super().__init__(self.message)


class UniqueViolation(ValueError):
    """Exception raised when a unique constraint is violated."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
