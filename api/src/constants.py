from enum import StrEnum, auto


class Table(StrEnum):
    """Database tables"""

    CUSTOM_EXCEPTIONS = auto()
    DEVICES = auto()
    RENTALS = auto()
    RESERVATIONS = auto()
