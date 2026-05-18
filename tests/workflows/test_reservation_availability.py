from unittest.mock import patch

from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses
from ui.src.data_service import DataService


class ReservationAvailabilityWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Reservation Availability page."""

    page_path = "ui/ui_pages/reservation_availability.py"

    def test_non_admin_no_update_controls(self):
        """Non-admin users see availability info but no controls to update limits."""
        at = self._run(MockAPIResponses(), auth_groups=[])
        self.assertEqual(
            0, len(at.number_input),
            "Non-admin should not see reservation limit number inputs",
        )
        update_buttons = [b for b in at.button if "Update" in b.label]
        self.assertEqual(0, len(update_buttons), "Non-admin should not see Update buttons")

    def test_admin_sees_update_controls(self):
        """Admin users see number inputs and Update buttons for each device type."""
        at = self._run(MockAPIResponses(), auth_groups=["cne-admin"])
        self.assertGreater(
            len(at.number_input), 0,
            "Admin should see reservation limit number inputs",
        )
        update_buttons = [b for b in at.button if "Update" in b.label]
        self.assertGreater(len(update_buttons), 0, "Admin should see Update buttons")

    def test_admin_update_limit_calls_service(self):
        """Clicking the Update button calls DataService.update_settings with the new limit."""
        at = self._run(MockAPIResponses(), auth_groups=["cne-admin"])
        update_buttons = [b for b in at.button if "Update" in b.label]
        self.assertGreater(len(update_buttons), 0)
        update_buttons[0].click()
        with patch.object(DataService, "update_settings") as mock_update:
            at = self._run(MockAPIResponses(), at=at)
            mock_update.assert_called_once()

    def test_admin_sets_limit_to_zero(self):
        """Admin can set the reservation limit to 0 — page renders without error."""
        at = self._run(MockAPIResponses(reservation_limit=0), auth_groups=["cne-admin"])
        self.assertEqual(0, len(at.error), "Page should render without errors even with limit=0")
        self.assertGreater(len(at.number_input), 0, "Limit inputs should still be visible when limit=0")
