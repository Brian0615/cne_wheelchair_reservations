# pylint: disable=missing-class-docstring,missing-function-docstring

from datetime import date, datetime, time
from unittest import TestCase
from unittest.mock import patch

import numpy as np

from common.constants import Location
from common.data_models import CompletedRental
from common.utils import get_default_timezone
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.rental_utils import submit_complete_rental_form
from ui.src.signature import Signature


class TestRentalUtils(TestCase):

    def setUp(self):
        pass

    @patch.object(CNEDates, attribute="get_cne_year", return_value=2024)
    @patch.object(DataService, attribute="complete_rental", return_value=(200, None))
    @patch("ui.src.rental_utils.display_complete_rental_success_dialog")
    def test_submit_complete_rental_form(self, mock_complete_rental, mock_success_dialog, _):
        mock_completed_rental = {
            "date": date(2024, 9, 1),
            "id": "W0901001",
            "name": "John Doe",
            "device_id": "W04",
            "return_date": date(2024, 9, 1),
            "return_time": time(15, 30),
            "return_location": Location.PG,
            "return_staff_name": "Test Staff",
            "return_signature": np.ones((100, 600, 4), dtype=np.uint8),
        }
        expected_called_with = CompletedRental(
            cne_year=2024,
            date=date(2024, 9, 1),
            id="W0901001",
            name="John Doe",
            device_id="W04",
            return_time=get_default_timezone().localize(datetime(2024, 9, 1, 15, 30)),
            return_location=Location.PG,
            return_staff_name="Test Staff",
            return_signature=Signature(signature_data=np.ones((100, 600, 4), dtype=np.uint8)).encode_as_base64(),
        )

        submit_complete_rental_form(mock_completed_rental)
        mock_complete_rental.assert_called_once_with(expected_called_with)
        mock_success_dialog.assert_called_once()
