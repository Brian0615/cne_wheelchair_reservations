from datetime import date, time
from typing import Tuple
from unittest.mock import MagicMock, patch

import numpy as np
from streamlit.testing.v1 import AppTest

from common.constants import DeviceType, Location
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests
from ui.src.constants import CNEDates


class TestCompleteRental(BaseTestCases.BaseUIPageTest):
    """Class for testing the Complete Rental page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/complete_rental.py"

    def _load_mock_rentals_data(self):
        scooter_rentals = self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="rentals")
        wheelchair_rentals = self._load_mock_data_from_json(device_type=DeviceType.WHEELCHAIR, data_type="rentals")
        return (
                [x for x in scooter_rentals if x["return_time"] is None]
                + [x for x in wheelchair_rentals if x["return_time"] is None]
        )

    # pylint: disable=no-member
    def test_rental_date_input(self):
        """Test if the provided input date range is correct"""
        self._test_date_input(key="complete_rental_date")

    # pylint: disable=no-member
    def test_select_rental_options(self):
        """Test that the correct number of rental options are provided"""

        mock_requests = MockRequests(mock_rentals_data=self._load_mock_rentals_data())
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        self.assertEqual(
            len(mock_requests.mock_rentals_data),
            len(at.selectbox[0].options),
            "Incorrect number of rentals displayed"
        )

    def _run_test_with_selected_rental(self, rental_index: int) -> Tuple[AppTest, MockRequests]:
        """Run a test with a selected rental"""

        with patch.object(
            CNEDates,
            attribute="get_cne_date_list",
            return_value=[date(2024, 8, 16), date(2024, 9, 2)],
        ):
            mock_requests = MockRequests(mock_rentals_data=self._load_mock_rentals_data())
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
            at.selectbox[0].select_index(rental_index)
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            return at, mock_requests

    def test_rental_without_items_left_behind(self):
        """Test the fields displayed when no items are left behind"""
        at, _ = self._run_test_with_selected_rental(rental_index=0)
        self.assertEqual(1, len(at.checkbox), "Only one checkbox should be displayed if no items left behind")
        self.assertTrue("Credit Card Deposit" in at.checkbox[0].label, "Incorrect deposit type displayed")

    def test_rental_with_items_left_behind(self):
        """Test the fields displayed when items are left behind"""
        at, _ = self._run_test_with_selected_rental(rental_index=3)
        self.assertEqual(2, len(at.checkbox), "Two checkboxes should be displayed if items left behind")
        self.assertTrue(
            "Items Left Behind" in at.checkbox[0].label
            and "Walker" in at.checkbox[0].label
            and "Stroller" in at.checkbox[0].label,
            "Incorrect items left behind checkbox displayed"
        )
        self.assertTrue("Cash Deposit" in at.checkbox[1].label, "Incorrect deposit type displayed")

    @patch(
        target="ui.src.constants.CNEDates.get_cne_date_list",
        return_value=[date(2024, 8, 16), date(2024, 9, 2)]
    )
    def test_complete_rental_form_submission(self, _):
        """Test the form submission for completing a rental"""
        with patch(
            target="ui.forms.form_fields.signature_field.st_canvas",
            return_value=MagicMock(image_data=np.ones((100, 600, 4), dtype=np.uint8))
        ):
            # select a rental
            at, mock_requests = self._run_test_with_selected_rental(rental_index=3)
            self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit button should be disabled")

            # fill in form
            at.time_input(key="complete_rental_return_time").set_value(time(14, 30))
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit button should be disabled")
            at.selectbox(key="complete_rental_return_location").set_value(Location.PG)
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit button should be disabled")
            at.text_input(key="complete_rental_staff_name").set_value("Test Staff")
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit button should be disabled")
            at.checkbox[0].set_value(True)
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit button should be disabled")
            at.checkbox[1].set_value(True)
            at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            self.assertFalse(at.button(key="complete_rental_submit").disabled, "Submit button should be enabled")
            at.button(key="complete_rental_submit").set_value(True)

            with patch("streamlit.success") as mock_success:
                self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
                mock_success.assert_called_once()
                success_msg = mock_success.call_args[0][0]
                mock_rental = mock_requests.mock_rentals_data[3]
                self.assertTrue("completed successfully" in success_msg, "Success message has incorrect contents")
                self.assertTrue(mock_rental["id"] in success_msg, "Rental ID should be in success message")
                self.assertTrue(mock_rental["name"] in success_msg, "Renter name should be in success message")
                self.assertTrue(mock_rental["device_id"] in success_msg, "Device ID should be in success message")
