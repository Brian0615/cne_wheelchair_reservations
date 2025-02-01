from common.constants import DeviceType
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests
from ui.src.constants import CNEDates


class TestViewRentals(BaseTestCases.BaseUIPageTest):
    """Class for testing the View Rentals page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/view_rentals.py"

    def test_rental_date_input(self):
        """Test if the provided input date range is correct"""
        self._test_date_input(key="view_rentals_date")

    def test_no_rentals(self):
        """Check the UI content for when there are no rentals"""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        today_date = CNEDates.get_default_date().strftime("%b %d, %Y")
        self.assertTrue(
            any("No Rentals" in warning.value and today_date in warning.value for warning in at.warning),
            "A warning message should be displayed that there are no Rentals"
        )
        self.assertEqual(0, len(at.subheader), "No subheaders for rentals should be displayed")
        self.assertEqual(0, len(at.dataframe), "No dataframes should be displayed as there is no data")

    def test_scooter_rentals_only(self):
        """Check the UI content for when there are only scooter rentals"""
        self._test_single_device_rentals_only(device_type=DeviceType.SCOOTER)

    def test_wheelchair_rentals_only(self):
        """Check the UI content for when there are only wheelchair rentals"""
        self._test_single_device_rentals_only(device_type=DeviceType.WHEELCHAIR)
