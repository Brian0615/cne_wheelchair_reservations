from datetime import time as time_type
from unittest.mock import Mock

import streamlit as st

from tests.shared_mock_data import MOCK_SCOOTER_INVENTORY, MOCK_SCOOTER_RESERVATIONS
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses


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

    def test_reservation_dropdown_populated_when_reservations_exist(self):
        """When reservations exist and all required header fields are set, the reservation dropdown appears."""

        responses = MockAPIResponses(
            inventory=MOCK_SCOOTER_INVENTORY,
            reservations=MOCK_SCOOTER_RESERVATIONS,
        )
        at = self._run_as_editor(responses)
        at.selectbox(key="new_rental_device_type").select("Scooter")
        at.selectbox(key="new_rental_pickup_location").select("BLC")
        at.time_input(key="new_rental_time").set_value(time_type(11, 0))
        at = self._run_as_editor(responses, at=at)
        # The reservation_id selectbox only appears after all required header fields are filled
        reservation_boxes = [s for s in at.selectbox if "reservation_id" in s.key]
        self.assertGreater(len(reservation_boxes), 0,
                           "Reservation selection should appear when all required fields are filled")
        # With reservations in the mock, options should include more than just Walk-In
        self.assertGreater(
            len(reservation_boxes[0].options), 1,
            "Reservation dropdown should include actual reservations, not just Walk-In",
        )

    def test_api_error_on_submit_shows_error(self):
        """When the API returns an error on rental creation, an error message is shown."""

        class RentalErrorResponses(MockAPIResponses):
            @staticmethod
            def put(url, *args, **kwargs):
                if "add_new_rental" in url:
                    return Mock(status_code=400, json=Mock(return_value="Device already rented"))
                return MockAPIResponses.put(url, *args, **kwargs)

        responses = MockAPIResponses(inventory=MOCK_SCOOTER_INVENTORY)
        error_responses = RentalErrorResponses(inventory=MOCK_SCOOTER_INVENTORY)
        at = self._run_as_editor(responses)
        at.selectbox(key="new_rental_device_type").select("Scooter")
        at.selectbox(key="new_rental_pickup_location").select("BLC")
        at.time_input(key="new_rental_time").set_value(time_type(11, 0))
        at = self._run_as_editor(responses, at=at)
        at.button(key="new_rental_submit").click()
        at = self._run_as_editor(error_responses, at=at, allow_errors=True)
        self.assertGreater(len(at.error), 0, "Expected an error message when rental creation fails")

    def _select_device_type_and_location(self, responses):
        """Helper: run the page then select Scooter device type, BLC location, and a pickup time."""
        at = self._run_as_editor(responses)
        at.selectbox(key="new_rental_device_type").select("Scooter")
        at.selectbox(key="new_rental_pickup_location").select("BLC")
        at.time_input(key="new_rental_time").set_value(time_type(11, 0))
        return self._run_as_editor(responses, at=at)

    def test_race_condition_selected_device_preserved_when_still_available(self):
        """When the available device list changes but the selected device is still in it, the selection is preserved."""
        responses = MockAPIResponses(inventory=MOCK_SCOOTER_INVENTORY)
        at = self._select_device_type_and_location(responses)
        at.selectbox(key="new_rental_device_id").select("S01")
        at = self._run_as_editor(responses, at=at)

        # Simulate cache TTL expiry: S02 is rented out but S01 is still available
        reduced_inventory = [d for d in MOCK_SCOOTER_INVENTORY if d["id"] != "S02"]
        reduced_responses = MockAPIResponses(inventory=reduced_inventory)
        st.cache_data.clear()
        at = self._run_as_editor(reduced_responses, at=at)

        self.assertEqual(
            "S01",
            at.selectbox(key="new_rental_device_id").value,
            "Selection should be preserved when the selected device is still available",
        )

    def test_race_condition_selected_device_cleared_when_no_longer_available(self):
        """When the available device list changes and the selected device is removed, the selection is cleared."""
        responses = MockAPIResponses(inventory=MOCK_SCOOTER_INVENTORY)
        at = self._select_device_type_and_location(responses)
        at.selectbox(key="new_rental_device_id").select("S01")
        at = self._run_as_editor(responses, at=at)

        # Simulate cache TTL expiry: S01 is now unavailable; only S02 remains
        reduced_inventory = [d for d in MOCK_SCOOTER_INVENTORY if d["id"] != "S01"]
        reduced_responses = MockAPIResponses(inventory=reduced_inventory)
        st.cache_data.clear()
        at = self._run_as_editor(reduced_responses, at=at)

        self.assertIsNone(
            at.selectbox(key="new_rental_device_id").value,
            "Selection should be cleared when the selected device is no longer available",
        )
