from common.constants import DeviceType
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests
from ui.src.constants import CNEDates


class TestHome(BaseTestCases.BaseUIPageTest):
    """Class for testing the Home page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/home.py"

    def test_no_reservations_or_rentals(self):
        """Test if there are no reservations or rentals"""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        today_date = CNEDates.get_default_date().strftime("%b %d, %Y")
        self.assertTrue(
            any("No Reservations Today" in warning.value and today_date in warning.value for warning in at.warning),
            "A warning message should be displayed that there are no reservations"
        )
        self.assertTrue(
            any("No Rentals Today" in warning.value and today_date in warning.value for warning in at.warning),
            "A warning message should be displayed that there are no Rentals"
        )
        self.assertEqual(0, len(at.subheader), "No subheaders for reservations or rentals should be displayed")
        self.assertEqual(0, len(at.dataframe), "No dataframes should be displayed as there is no data")

    def test_single_device_reservations_only(self):
        """Check the UI content for when there are only reservations for one device type"""
        for device_type in DeviceType:
            with self.subTest(device_type=device_type):
                self._subtest_single_device_reservations_only(device_type=device_type)

    def test_single_device_rentals_only(self):
        """Check the UI content for when there are only rentals for one device type"""
        for device_type in DeviceType:
            with self.subTest(device_type=device_type):
                self._subtest_single_device_rentals_only(device_type=device_type)
