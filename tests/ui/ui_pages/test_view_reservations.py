from common.constants import DeviceType
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests
from ui.src.constants import CNEDates


class TestViewReservations(BaseTestCases.BaseUIPageTest):
    """Class for testing the View Reservations page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/view_reservations.py"

    def test_reservation_date_input(self):
        """Test if the provided input date range is correct"""
        self._test_date_input(key="view_reservations_date")

    def test_no_reservations(self):
        """Check the UI content for when there are no reservations"""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        today_date = CNEDates.get_default_date().strftime("%b %d, %Y")
        self.assertTrue(
            any("No Reservations" in warning.value and today_date in warning.value for warning in at.warning),
            "A warning message should be displayed that there are no reservations"
        )
        self.assertEqual(0, len(at.subheader), "No subheaders for reservations should be displayed")
        self.assertEqual(0, len(at.dataframe), "No dataframes should be displayed as there is no data")

    def test_scooter_reservations_only(self):
        """Check the UI content for when there are only scooter reservations"""
        self._test_single_device_reservations_only(device_type=DeviceType.SCOOTER)

    def test_wheelchair_reservations_only(self):
        """Check the UI content for when there are only wheelchair reservations"""
        self._test_single_device_reservations_only(device_type=DeviceType.WHEELCHAIR)
