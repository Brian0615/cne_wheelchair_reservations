from tests.unit.base_tests import BaseTestCases


class TestManageReservations(BaseTestCases.BaseUIPageTest):
    """Class for testing the Manage Reservations page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/manage_reservation.py"
