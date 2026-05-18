from tests.unit.base_tests import BaseTestCases


class TestCompleteRental(BaseTestCases.BaseUIPageTest):
    """Class for testing the Complete Rental page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/complete_rental.py"

    def test_rental_date_input(self):
        """Test if the provided input date range is correct"""
        self._test_date_input(key="complete_rental_date")
