import os
from datetime import date, datetime, time, timedelta
from enum import StrEnum, auto
from typing import List, Tuple

from common.constants import ReservationStatus
from common.utils import get_default_timezone


class CNEDates:
    """Class for determining dates of the CNE"""
    __CNE_DURATION_DAYS = 18

    @classmethod
    def get_cne_year(cls):
        """Get the CNE year from the environment variable or the current year"""
        return int(os.getenv("CNE_YEAR", datetime.now(tz=get_default_timezone()).year))

    @classmethod
    def get_cne_start_end_dates(cls) -> Tuple[datetime, datetime]:
        """Get the start and end dates of the CNE for a given year. If no year is provided, the current year is used."""
        # get first Monday of September by taking Sept 7 and subtracting the weekday
        end_date = datetime(cls.get_cne_year(), 9, 7)
        end_date = end_date - timedelta(days=end_date.weekday())
        start_date = end_date - timedelta(days=CNEDates.__CNE_DURATION_DAYS - 1)
        return start_date, end_date

    @classmethod
    def get_cne_date_list(cls) -> List[date]:
        """Get a list of all dates of the CNE for a given year. If no year is provided, the current year is used."""
        start_date, end_date = cls.get_cne_start_end_dates()
        return [(start_date + timedelta(days=i)).date() for i in range((end_date - start_date).days + 1)]

    @classmethod
    def get_default_date(cls):
        """Get the default date for displaying reservations - today's date bounded by CNE dates"""
        all_dates = cls.get_cne_date_list()
        return min(
            max(all_dates),
            max(min(all_dates), datetime.now(tz=get_default_timezone()).date()),
        )

    @classmethod
    def get_default_new_reservation_date(cls):
        """Get the default reservation date for the reservation form - tomorrow's date bounded by CNE dates"""
        all_dates = cls.get_cne_date_list()
        return min(
            max(all_dates),
            max(min(all_dates), datetime.now(tz=get_default_timezone()).date() + timedelta(days=1))
        )

    @classmethod
    def get_default_new_reservation_time(cls):
        """Get the default reservation time for the reservation form - 10:00 AM"""
        return time(hour=10)


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
            case ReservationStatus.CANCELLED:
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
