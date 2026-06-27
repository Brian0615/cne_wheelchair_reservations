from tests.unit.base_tests import BaseTestCases
from tests.unit.mock_requests import MockRequests


class TestNewReservation(BaseTestCases.BaseUIPageTest):
    """Class for testing the New Reservation page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/new_reservation.py"

    def test_checkbox_present_in_form(self):
        """The Add to Waitlist (Override) checkbox is rendered as part of the new reservation form"""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())
        checkbox = at.checkbox(key="new_reservation_force_waitlist")
        self.assertEqual("Add to Waitlist (Override)", checkbox.label)
        self.assertFalse(checkbox.value, "Checkbox should be unchecked by default")
        self.assertFalse(checkbox.disabled)
