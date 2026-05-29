from tests.shared_mock_data import MOCK_SCOOTER_INVENTORY, MOCK_WHEELCHAIR_INVENTORY, MOCK_FULL_INVENTORY
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses


class ViewInventoryWorkflowTests(WorkflowTestCase):
    """Workflow tests for the View Inventory page."""

    page_path = "ui/ui_pages/view_inventory.py"

    def test_empty_inventory_shows_warning(self):
        """When inventory is empty, warnings are shown for both device types."""
        at = self._run(MockAPIResponses())
        self.assertTrue(
            any("No Scooters" in w.value for w in at.warning),
            "Expected 'No Scooters' warning when scooter inventory is empty",
        )
        self.assertTrue(
            any("No Wheelchairs" in w.value for w in at.warning),
            "Expected 'No Wheelchairs' warning when wheelchair inventory is empty",
        )
        self.assertEqual(0, len(at.dataframe), "No dataframes should appear for empty inventory")

    def test_inventory_displays_tables(self):
        """When inventory exists, tables are shown for each device type present."""
        responses = MockAPIResponses(inventory=MOCK_FULL_INVENTORY)
        at = self._run(responses)
        self.assertFalse(
            any("No Scooters" in w.value for w in at.warning),
            "Should not show 'No Scooters' warning when scooter inventory exists",
        )
        self.assertFalse(
            any("No Wheelchairs" in w.value for w in at.warning),
            "Should not show 'No Wheelchairs' warning when wheelchair inventory exists",
        )
        self.assertGreater(len(at.dataframe), 0, "Inventory dataframe should be displayed")

    def test_status_filter_reduces_displayed_rows(self):
        """Selecting a status filter reduces the rows shown in the inventory table."""
        responses = MockAPIResponses(inventory=MOCK_SCOOTER_INVENTORY)
        at = self._run(responses)
        at.selectbox(key="scooter_status_filter").select("Available")
        at = self._run(responses, at=at)
        self.assertEqual(1, len(at.dataframe), "One filtered dataframe should be shown")
        expected_count = sum(1 for d in MOCK_SCOOTER_INVENTORY if d["status"] == "Available")
        self.assertEqual(expected_count, len(at.dataframe[0].value))

    def test_location_filter_reduces_displayed_rows(self):
        """Selecting a location filter reduces the rows shown in the inventory table."""
        responses = MockAPIResponses(inventory=MOCK_SCOOTER_INVENTORY)
        at = self._run(responses)
        at.selectbox(key="scooter_location_filter").select("BLC")
        at = self._run(responses, at=at)
        self.assertEqual(1, len(at.dataframe), "One filtered dataframe should be shown")
        expected_count = sum(1 for d in MOCK_SCOOTER_INVENTORY if d["location"] == "BLC")
        self.assertEqual(expected_count, len(at.dataframe[0].value))

    def test_single_device_type_inventory_shows_warning_for_other(self):
        """When only one device type has inventory, a warning is shown for the missing device type."""
        for inventory, device_name, other_name in [
            (MOCK_SCOOTER_INVENTORY, "Scooter", "Wheelchair"),
            (MOCK_WHEELCHAIR_INVENTORY, "Wheelchair", "Scooter"),
        ]:
            with self.subTest(device=device_name):
                at = self._run(MockAPIResponses(inventory=inventory))
                self.assertFalse(
                    any(f"No {device_name}s" in w.value for w in at.warning),
                    f"Should not warn about {device_name}s when they exist",
                )
                self.assertTrue(
                    any(f"No {other_name}s" in w.value for w in at.warning),
                    f"Should warn that there are no {other_name}s",
                )
                self.assertEqual(1, len(at.dataframe), "Exactly one device type table should be shown")
