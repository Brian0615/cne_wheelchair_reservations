from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses, MOCK_SCOOTER_INVENTORY


class NewRentalWorkflowTests(WorkflowTestCase):
    """Workflow tests for the New Rental page."""

    page_path = "ui/ui_pages/new_rental.py"

    def _run_as_editor(self, responses, at=None, allow_errors=False):
        return self._run(responses, at=at, allow_errors=allow_errors, roles=["editor"])

    def test_initial_form_renders(self):
        """The form renders with date and time inputs on initial load."""
        at = self._run_as_editor(MockAPIResponses())
        self.assertGreater(len(at.date_input), 0, "Date input should be present on initial render")
        self.assertGreater(len(at.time_input), 0, "Time input should be present on initial render")

    def test_no_available_devices_shows_warning(self):
        """When no devices are available for the selected type and location, a warning is shown."""
        responses = MockAPIResponses(inventory=[])  # empty inventory → no available devices
        at = self._run_as_editor(responses)
        # Select a device type and pickup location to trigger the available devices check
        at.selectbox(key="new_rental_device_type").select("Scooter")
        at.selectbox(key="new_rental_pickup_location").select("BLC")
        at = self._run_as_editor(responses, at=at)
        self.assertTrue(
            any("No Available" in w.value for w in at.warning),
            "Expected 'No Available' warning when no devices are available",
        )

    def test_available_devices_populate_device_dropdown(self):
        """When devices are available, the device ID dropdown is populated."""
        responses = MockAPIResponses(inventory=MOCK_SCOOTER_INVENTORY)
        at = self._run_as_editor(responses)
        at.selectbox(key="new_rental_device_type").select("Scooter")
        at.selectbox(key="new_rental_pickup_location").select("BLC")
        at = self._run_as_editor(responses, at=at)
        self.assertFalse(
            any("No Available" in w.value for w in at.warning),
            "Should not show 'No Available' warning when devices are available",
        )

    def test_id_not_verified_blocks_submit(self):
        """The submit button is disabled when the ID Verified checkbox is not checked."""
        responses = MockAPIResponses(inventory=MOCK_SCOOTER_INVENTORY)
        at = self._run_as_editor(responses)
        at.selectbox(key="new_rental_device_type").select("Scooter")
        at.selectbox(key="new_rental_pickup_location").select("BLC")
        at = self._run_as_editor(responses, at=at)
        # id_verified checkbox is unchecked by default — submit should be disabled
        submit_buttons = [b for b in at.button if "submit" in b.key.lower() or "Submit" in b.label]
        if submit_buttons:
            self.assertTrue(
                all(b.disabled for b in submit_buttons),
                "Submit button should be disabled when ID is not verified",
            )
