from tests.unit.base_tests import BaseTestCases


class TestViewReservations(BaseTestCases.BaseUIPageTest):
    """Class for testing the View Reservations page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/view_reservations.py"

    def test_reservation_date_input(self):
        """Test if the provided input date range is correct"""
        self._test_date_input(key="view_reservations_date")
