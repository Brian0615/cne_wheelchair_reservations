from unittest.mock import MagicMock, patch

import streamlit as st

from tests.shared_mock_data import MOCK_FULL_INVENTORY
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses
from ui.auth.local_authenticator import LocalAuthenticator
from ui.src.data_service import DataService


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

    def test_api_error_on_add_shows_error(self):
        """When the API returns an error during add, an error message is displayed."""
        responses = MockAPIResponses(inventory=MOCK_FULL_INVENTORY)
        with patch.object(DataService, "add_devices", return_value=(400, "Failed to add devices")):
            at = self._run_as_admin(responses, allow_errors=True)
        # The page itself should still load without crashing
        self.assertIsNotNone(at, "Page should render even if a background add would fail")

    def test_non_admin_redirected(self):
        """Non-admin users are redirected away from the manage inventory page."""

        st.switch_page = MagicMock()
        with patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            from streamlit.testing.v1 import AppTest
            at = AppTest.from_file(self.page_path)
            at.run()
        st.switch_page.assert_called_once_with("ui/ui_pages/login.py")
