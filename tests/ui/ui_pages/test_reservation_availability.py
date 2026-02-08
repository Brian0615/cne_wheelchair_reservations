from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests


class TestReservationAvailability(BaseTestCases.BaseUIPageTest):
    """Class for testing the View Reservations page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/reservation_availability.py"

    def test_no_reservation_limit(self):
        """Check the UI content for when there is no reservation limit set"""
        self._run_app_test_with_mock_requests(mock_requests=MockRequests())
