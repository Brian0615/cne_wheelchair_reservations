from datetime import datetime

from common.utils import get_default_timezone
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests


class TestNewRental(BaseTestCases.BaseUIPageTest):
    """Class for testing the New Rental page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/new_rental.py"

    def test_new_rental_time(self):
        """Check that the default time in a new rental form is in the correct timezone"""
        current_time = datetime.now(tz=get_default_timezone())
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        self.assertLessEqual(
            abs(
                (
                        get_default_timezone().localize(
                            datetime.combine(current_time.date(), at.time_input[0].value)
                        ) - current_time
                ).total_seconds()
            ),
            120,
            "Displayed time on new rental form is incorrect or in the wrong timezone"
        )
