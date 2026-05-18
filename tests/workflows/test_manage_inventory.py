from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses, MOCK_FULL_INVENTORY


class ManageInventoryWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Manage Inventory page."""

    page_path = "ui/ui_pages/manage_inventory.py"

    def _run_as_admin(self, responses, at=None, allow_errors=False):
        return self._run(responses, at=at, allow_errors=allow_errors, roles=["admin"])

    def test_empty_inventory_shows_warning(self):
        """When inventory is empty, warnings are shown for both device types."""
        at = self._run_as_admin(MockAPIResponses())
        self.assertTrue(
            any("No Scooters" in w.value for w in at.warning),
            "Expected 'No Scooters' warning when scooter inventory is empty",
        )
        self.assertTrue(
            any("No Wheelchairs" in w.value for w in at.warning),
            "Expected 'No Wheelchairs' warning when wheelchair inventory is empty",
        )

    def test_inventory_loads_and_displays_tables(self):
        """When inventory exists, tables are displayed for both device types."""
        responses = MockAPIResponses(inventory=MOCK_FULL_INVENTORY)
        at = self._run_as_admin(responses)
        self.assertFalse(
            any("No Scooters" in w.value for w in at.warning),
            "Should not show 'No Scooters' when scooter inventory exists",
        )
        self.assertFalse(
            any("No Wheelchairs" in w.value for w in at.warning),
            "Should not show 'No Wheelchairs' when wheelchair inventory exists",
        )
        self.assertGreater(len(at.dataframe), 0, "Inventory dataframes should be shown")

    def test_action_buttons_present_for_each_device_type(self):
        """Add, Update, Transfer, and Remove buttons are present for both device types."""
        responses = MockAPIResponses(inventory=MOCK_FULL_INVENTORY)
        at = self._run_as_admin(responses)
        for device in ("scooters", "wheelchairs"):
            for action in ("add", "update", "transfer", "remove"):
                key = f"manage_inventory_{action}_{device}"
                matching = [b for b in at.button if b.key == key]
                self.assertEqual(1, len(matching), f"Button '{key}' should be present")
