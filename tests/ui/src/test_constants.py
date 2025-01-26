import unittest
from datetime import datetime
from unittest.mock import patch

from common.utils import get_default_timezone
from ui.src import constants
from ui.src.constants import CNEDates


class TestCNEDates(unittest.TestCase):
    """Test the CNEDates class."""

    def test_get_cne_start_end_dates(self):
        """Test the get_cne_start_end_dates method."""
        # make datetime.today return a date in 2021
        with patch.object(constants, "datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2021, 12, 11, tzinfo=get_default_timezone())
            mock_datetime.side_effect = datetime

            start_date, end_date = CNEDates.get_cne_start_end_dates()
            self.assertEqual(datetime(2021, 8, 20), start_date)
            self.assertEqual(datetime(2021, 9, 6), end_date)

    def test_get_cne_date_list(self):
        """Test the get_cne_date_list method."""
        # make datetime.today return a date in 2025
        with patch.object(constants, "datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 12, 11, tzinfo=get_default_timezone())
            mock_datetime.side_effect = datetime

            dates = CNEDates.get_cne_date_list()
            # dates should be a list from Aug 15, 2025 to Sep 1, 2025
            self.assertEqual(
                [
                    datetime(2025, 8, 15).date(),
                    datetime(2025, 8, 16).date(),
                    datetime(2025, 8, 17).date(),
                    datetime(2025, 8, 18).date(),
                    datetime(2025, 8, 19).date(),
                    datetime(2025, 8, 20).date(),
                    datetime(2025, 8, 21).date(),
                    datetime(2025, 8, 22).date(),
                    datetime(2025, 8, 23).date(),
                    datetime(2025, 8, 24).date(),
                    datetime(2025, 8, 25).date(),
                    datetime(2025, 8, 26).date(),
                    datetime(2025, 8, 27).date(),
                    datetime(2025, 8, 28).date(),
                    datetime(2025, 8, 29).date(),
                    datetime(2025, 8, 30).date(),
                    datetime(2025, 8, 31).date(),
                    datetime(2025, 9, 1).date(),
                ],
                dates
            )

    def test_get_default_date(self):
        with patch.object(constants, "datetime") as mock_datetime:
            mock_datetime.side_effect = datetime

            # test a date before the CNE
            mock_datetime.now.return_value = datetime(2025, 8, 11, tzinfo=get_default_timezone())
            self.assertEqual(datetime(2025, 8, 15).date(), CNEDates.get_default_date())

            # test a date during the CNE
            mock_datetime.now.return_value = datetime(2025, 8, 20, tzinfo=get_default_timezone())
            self.assertEqual(datetime(2025, 8, 20).date(), CNEDates.get_default_date())

            # test a date after the CNE
            mock_datetime.now.return_value = datetime(2025, 12, 11, tzinfo=get_default_timezone())
            self.assertEqual(datetime(2025, 9, 1).date(), CNEDates.get_default_date())

    def test_get_new_default_reservation_date(self):
        """Test the get_default_new_reservation_date method."""
        with patch.object(constants, "datetime") as mock_datetime:
            mock_datetime.side_effect = datetime

            # test a date before the CNE
            mock_datetime.now.return_value = datetime(2025, 8, 11, tzinfo=get_default_timezone())
            self.assertEqual(datetime(2025, 8, 15).date(), CNEDates.get_default_new_reservation_date())

            # test a date during the CNE (DEFAULT RESERVATION DATE SHOULD BE ONE DAY AHEAD)
            mock_datetime.now.return_value = datetime(2025, 8, 20, tzinfo=get_default_timezone())
            self.assertEqual(datetime(2025, 8, 21).date(), CNEDates.get_default_new_reservation_date())

            # test a date after the CNE
            mock_datetime.now.return_value = datetime(2025, 12, 11, tzinfo=get_default_timezone())
            self.assertEqual(datetime(2025, 9, 1).date(), CNEDates.get_default_new_reservation_date())
