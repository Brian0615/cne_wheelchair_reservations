from enum import StrEnum, auto

from common.constants import ReservationStatus


class Colour(StrEnum):
    """Colour Constants"""

    # Reservation Availability Heatmap Colours
    RESERVATIONS_AVAILABLE = "#479825"
    RESERVATIONS_LOW = "#F5AB4B"
    RESERVATIONS_NONE = "#DF4E46"

    # Reservations Export PDF Colours
    TABLE_HEADER = "#89CFF1"
    TABLE_ALTERNATE_LIGHT_GREY = "#E5E5E5"

    # Reservation Table Colours
    RESERVATION_TABLE_CANCELLED = "#FCDEDE"
    RESERVATION_TABLE_READY = "#E1F8FC"
    RESERVATION_TABLE_COMPLETED = "#E1FCE1"
    RESERVATION_TABLE_PENDING = "#F7E7D5"

    # Indicator
    INDICATOR_RED = "#DF4E46"
    INDICATOR_ORANGE = "#F5AB4B"
    INDICATOR_GREEN = "#479825"

    @classmethod
    def get_reservation_table_status_colour(cls, status: ReservationStatus):
        """Get the colour for a reservation status for the reservation table"""
        match status:
            case ReservationStatus.CANCELLED | ReservationStatus.NO_SHOW:
                return cls.RESERVATION_TABLE_CANCELLED
            case ReservationStatus.CONFIRMED | ReservationStatus.RESERVED:
                return cls.RESERVATION_TABLE_READY
            case ReservationStatus.COMPLETED | ReservationStatus.PICKED_UP:
                return cls.RESERVATION_TABLE_COMPLETED
            case ReservationStatus.PENDING | ReservationStatus.WAITLISTED:
                return cls.RESERVATION_TABLE_PENDING
            case _:
                return "#FFFFFF"  # Default to white for other statuses


class Page(StrEnum):
    """Page Name"""
    VIEW_RENTALS = auto()
    VIEW_RESERVATIONS = auto()
