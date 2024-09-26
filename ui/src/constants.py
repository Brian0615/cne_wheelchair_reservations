from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple


class CNEDates:
    """Class for determining dates of the CNE"""
    __CNE_DURATION_DAYS = 18

    @classmethod
    def get_cne_start_end_dates(cls, year: Optional[int] = None) -> Tuple[datetime, datetime]:
        """Get the start and end dates of the CNE for a given year. If no year is provided, the current year is used."""
        end_date = datetime(year if year is not None else datetime.today().year, 9, 7)
        end_date = end_date - timedelta(days=end_date.weekday())
        start_date = end_date - timedelta(days=CNEDates.__CNE_DURATION_DAYS - 1)
        return start_date, end_date

    @classmethod
    def get_cne_date_list(cls, year: Optional[int] = None) -> List[date]:
        """Get a list of all dates of the CNE for a given year. If no year is provided, the current year is used."""
        start_date, end_date = cls.get_cne_start_end_dates(year=year)
        return [(start_date + timedelta(days=i)).date() for i in range((end_date - start_date).days + 1)]

    @classmethod
    def get_default_reservation_date(cls):
        """Get the default reservation date for the reservation form."""
        all_dates = cls.get_cne_date_list(year=datetime.today().year)
        return min(max(all_dates), max(min(all_dates), datetime.today().date() + timedelta(days=1)))
