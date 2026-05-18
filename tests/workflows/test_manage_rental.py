from unittest.mock import Mock, patch

from tests.shared_mock_data import MOCK_SCOOTER_RENTALS, MOCK_SCOOTER_INVENTORY
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses
from ui.src.data_service import DataService


class ManageRentalWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Manage Rental page."""

    page_path = "ui/ui_pages/manage_rental.py"

    def _run_as_editor(self, responses, at=None, allow_errors=False):
        return self._run(responses, at=at, allow_errors=allow_errors, roles=["editor"])

    def _select_rental_and_location(self, responses):
        """Helper: run the page, select the first rental and first location."""
        at = self._run_as_editor(responses)
        at.selectbox(key="manage_rental_rental_selection").select_index(0)
        at = self._run_as_editor(responses, at=at)
        at.selectbox(key="change_device_location").select_index(0)
        at = self._run_as_editor(responses, at=at)
        return at

    def test_no_available_devices_shows_warning(self):
        """When a location is selected but no devices are available, a warning is shown."""
        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS, inventory=[])
        at = self._select_rental_and_location(responses)
        self.assertTrue(
            any("No Available Devices" in w.value for w in at.warning),
            "Expected 'No Available Devices' warning when inventory is empty",
        )

    def test_download_button_present_when_rental_selected(self):
        """After selecting a rental, a download button for the rental form is present.

        AppTest does not expose st.download_button via at.download_button in Streamlit 1.57.
        We verify no error is shown (meaning the form was fetched successfully).
        """
        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS, inventory=MOCK_SCOOTER_INVENTORY)
        at = self._run_as_editor(responses)
        at.selectbox(key="manage_rental_rental_selection").select_index(0)
        at = self._run_as_editor(responses, at=at)
        self.assertFalse(
            any("Unable to find rental form" in e.value for e in at.error),
            "Rental form download should succeed without errors",
        )

    def test_change_device_submit_calls_service(self):
        """Filling all change-device fields and clicking Submit calls DataService.change_rental_device."""
        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS, inventory=MOCK_SCOOTER_INVENTORY)
        at = self._select_rental_and_location(responses)
        at.selectbox(key="change_device_new_device_id").select_index(0)
        at.text_input(key="change_device_staff_name").set_value("Test Staff")
        # Run once so the button captures the filled args before the click fires them
        at = self._run_as_editor(responses, at=at)
        at.button(key="change_device_submit_button").click()
        with patch.object(DataService, "change_rental_device") as mock_change:
            at = self._run_as_editor(responses, at=at)
            mock_change.assert_called_once()

    def test_submit_button_absent_when_no_devices(self):
        """When no devices are available at the selected location, the submit button is not rendered."""
        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS, inventory=[])
        at = self._select_rental_and_location(responses)
        submit_buttons = [b for b in at.button if "change_device_submit_button" in b.key]
        self.assertEqual(0, len(submit_buttons), "Submit button should not appear when no devices are available")

    def test_cache_cleared_after_device_change(self):
        """After a successful device change, the rentals and inventory caches are cleared."""
        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS, inventory=MOCK_SCOOTER_INVENTORY)
        at = self._select_rental_and_location(responses)
        at.selectbox(key="change_device_new_device_id").select_index(0)
        at.text_input(key="change_device_staff_name").set_value("Test Staff")
        at = self._run_as_editor(responses, at=at)
        at.button(key="change_device_submit_button").click()
        with patch.object(DataService, "get_rentals_on_date") as mock_rentals, \
                patch.object(DataService, "get_available_device_ids") as mock_devices:
            self._run_as_editor(responses, at=at)
            mock_rentals.clear.assert_called_once()
            mock_devices.clear.assert_called_once()

    def test_api_error_on_change_device_shows_error(self):
        """When the API returns an error on change device, an error or exception is surfaced."""

        class ChangeDeviceErrorResponses(MockAPIResponses):
            @staticmethod
            def post(url, *args, **kwargs):
                if "change_device" in url:
                    return Mock(status_code=400, json=Mock(return_value="Device unavailable"))
                return MockAPIResponses.post(url, *args, **kwargs)

        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS, inventory=MOCK_SCOOTER_INVENTORY)
        error_responses = ChangeDeviceErrorResponses(rentals=MOCK_SCOOTER_RENTALS, inventory=MOCK_SCOOTER_INVENTORY)
        at = self._select_rental_and_location(responses)
        at.selectbox(key="change_device_new_device_id").select_index(0)
        at.text_input(key="change_device_staff_name").set_value("Test Staff")
        at = self._run_as_editor(responses, at=at)
        at.button(key="change_device_submit_button").click()
        at = self._run_as_editor(error_responses, at=at, allow_errors=True)
        self.assertGreater(len(at.error), 0, "Expected an error message when device change fails")
