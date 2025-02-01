from tests.base_tests import BaseTestCases


class TestNewReservation(BaseTestCases.BaseUIPageTest):
    """Class for testing the New Reservation page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/new_reservation.py"
