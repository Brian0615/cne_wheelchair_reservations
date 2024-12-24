import unittest
from datetime import datetime
from unittest.mock import patch

from ui.src import constants
from ui.src.constants import CNEDates


class TestCNEDates(unittest.TestCase):
    """Test the CNEDates class."""

    def test_get_cne_start_end_dates(self):
        """Test the get_cne_start_end_dates method."""
        # make datetime.today return a date in 2021
        with patch.object(constants, "datetime") as mock_datetime:
            mock_datetime.today.return_value = datetime(2021, 1, 1)
            mock_datetime.side_effect = datetime

            # call the function
            start_date, end_date = CNEDates.get_cne_start_end_dates()
            # check the return values
            self.assertEqual(datetime(2021, 8, 20), start_date)
            self.assertEqual(datetime(2021, 9, 6), end_date)

    def test_get_new_default_reservation_date(self):
        # make datetime.today return a date in 2021
        with patch.object(constants, "datetime") as mock_datetime:
            mock_datetime.today.return_value = datetime(2021, 12, 11)
            mock_datetime.side_effect = datetime

            # call the function
            new_date = CNEDates.get_default_new_reservation_date()
            # check the return values
            self.assertEqual(datetime(2021, 9, 6).date(), new_date)
