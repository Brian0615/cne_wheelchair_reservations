from tests.unit.base_tests import BaseTestCases


class TestViewRentals(BaseTestCases.BaseUIPageTest):
    """Class for testing the View Rentals page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/view_rentals.py"

    def test_rental_date_input(self):
        """Test if the provided input date range is correct"""
        self._test_date_input(key="view_rentals_date")
