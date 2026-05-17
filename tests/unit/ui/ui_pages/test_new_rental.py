from tests.unit.base_tests import BaseTestCases
from tests.unit.mock_requests import MockRequests


class TestNewRental(BaseTestCases.BaseUIPageTest):
    """Class for testing the New Rental page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/new_rental.py"

    def test_new_rental_time(self):
        """Check that the default time in a new rental form is in the correct timezone"""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())
        self.assertIsNone(at.time_input[0].value)  # pylint: disable=no-member
