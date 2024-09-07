import unittest
from datetime import datetime
from unittest.mock import patch

from ui.src import constants
from ui.src.constants import CNEDates


class TestCNEDates(unittest.TestCase):

    def test_get_cne_start_end_dates(self):
        # make datetime.today return a date in 2024
        with patch.object(constants, "datetime") as mock_datetime:
            mock_datetime.today.return_value = datetime(2021, 1, 1)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            # call the function
            start_date, end_date = CNEDates.get_cne_start_end_dates()
            # check the return values
            self.assertEqual(datetime(2021, 8, 20), start_date)
            self.assertEqual(datetime(2021, 9, 6), end_date)
