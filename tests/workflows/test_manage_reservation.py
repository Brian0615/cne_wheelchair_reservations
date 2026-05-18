from unittest.mock import patch

from common.constants import ReservationStatus
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses, MOCK_SCOOTER_RESERVATIONS
from ui.src import reservation_utils, utils
from ui.src.data_service import DataService

# Reservations by status for targeted testing
_EDITABLE_RESERVATION = [r for r in MOCK_SCOOTER_RESERVATIONS if r["status"] == "Reserved"][0]
_TERMINAL_STATUSES = ["Picked Up", "Completed", "Cancelled"]
_TERMINAL_RESERVATIONS = [r for r in MOCK_SCOOTER_RESERVATIONS if r["status"] in _TERMINAL_STATUSES]


class ManageReservationWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Manage Reservation page."""

    page_path = "ui/ui_pages/manage_reservation.py"

    def _run_as_admin(self, responses, at=None, allow_errors=False):
        return self._run(responses, at=at, allow_errors=allow_errors, roles=["admin"])

    def _load_reservations_and_select(self, responses, index=0):
        """Helper: run the page and select a reservation by index."""
        at = self._run_as_admin(responses)
        at.selectbox(key="manage_reservations_id_selection").select_index(index)
        at = self._run_as_admin(responses, at=at)
        return at

    def test_no_reservations_shows_warning(self):
        """When no reservations exist for the selected date, a warning is shown."""
        at = self._run_as_admin(MockAPIResponses())
        self.assertTrue(
            any("No Reservations" in w.value for w in at.warning),
            "Expected 'No Reservations' warning when no data exists",
        )
        id_selection_boxes = [s for s in at.selectbox if "id_selection" in s.key]
        self.assertEqual(0, len(id_selection_boxes), "Reservation selection should not appear when no data exists")

    def test_confirm_reservation_calls_service(self):
        """Clicking Confirm calls update_reservation_status with CONFIRMED status."""
        responses = MockAPIResponses(reservations=[_EDITABLE_RESERVATION])
        at = self._load_reservations_and_select(responses)
        at.button(key="confirm_reservation").click()
        with patch.object(DataService, "update_reservation_status") as mock_update:
            at = self._run_as_admin(responses, at=at)
            mock_update.assert_called_once()
            _, kwargs = mock_update.call_args
            self.assertEqual(ReservationStatus.CONFIRMED, kwargs.get("status"))

    def test_cancel_reservation_calls_service(self):
        """Clicking Cancel calls update_reservation_status with CANCELLED status."""
        responses = MockAPIResponses(reservations=[_EDITABLE_RESERVATION])
        at = self._load_reservations_and_select(responses)
        at.button(key="cancel_reservation").click()
        with patch.object(DataService, "update_reservation_status") as mock_update:
            at = self._run_as_admin(responses, at=at)
            mock_update.assert_called_once()
            _, kwargs = mock_update.call_args
            self.assertEqual(ReservationStatus.CANCELLED, kwargs.get("status"))

    def test_update_reservation_details_calls_submit(self):
        """Changing a field and submitting calls submit_update_reservation_form."""
        responses = MockAPIResponses(reservations=[_EDITABLE_RESERVATION])
        at = self._load_reservations_and_select(responses)
        at.text_input(key="update_reservation_name").set_value("Updated Name")
        at.button(key="update_reservation_submit").click()
        with patch.object(reservation_utils, "submit_update_reservation_form") as mock_submit:
            at = self._run_as_admin(responses, at=at)
            mock_submit.assert_called_once()

    def test_terminal_status_disables_confirm_and_cancel(self):
        """Reservations in terminal states (Picked Up, Completed, Cancelled) have disabled action buttons.

        Cancelled reservations show their status via st.error() (red badge), so allow_errors=True.
        """
        for reservation in _TERMINAL_RESERVATIONS:
            with self.subTest(status=reservation["status"]):
                responses = MockAPIResponses(reservations=[reservation])
                at = self._run_as_admin(responses)
                at.selectbox(key="manage_reservations_id_selection").select_index(0)
                at = self._run_as_admin(responses, at=at, allow_errors=True)
                confirm_btn = at.button(key="confirm_reservation")
                cancel_btn = at.button(key="cancel_reservation")
                self.assertTrue(confirm_btn.disabled, f"Confirm should be disabled for status {reservation['status']}")
                self.assertTrue(cancel_btn.disabled, f"Cancel should be disabled for status {reservation['status']}")

    def test_switch_selected_reservation_updates_form(self):
        """Switching the selected reservation updates the name field in the form."""
        responses = MockAPIResponses(reservations=MOCK_SCOOTER_RESERVATIONS)
        at = self._load_reservations_and_select(responses, index=0)
        first_name = at.text_input(key="update_reservation_name").value

        at.selectbox(key="manage_reservations_id_selection").select_index(1)
        at = self._run_as_admin(responses, at=at)
        second_name = at.text_input(key="update_reservation_name").value

        self.assertNotEqual(first_name, second_name, "Form should update when a different reservation is selected")

    def test_reservation_dropdown_format(self):
        """Reservation options are formatted as 'ID - Name (HH:MM AM/PM, Location)'."""
        responses = MockAPIResponses(reservations=MOCK_SCOOTER_RESERVATIONS)
        at = self._run_as_admin(responses)
        options = at.selectbox(key="manage_reservations_id_selection").options
        # First option (sorted by ID): S0820001 - Alice Smith - BLC - 10:00 AM
        self.assertEqual("S0820001 - Alice Smith (10:00 AM, BLC)", options[0])

    def test_all_status_field_states(self):
        """Confirm/Cancel buttons and form fields are enabled/disabled correctly for every reservation status."""
        all_statuses = {r["status"] for r in MOCK_SCOOTER_RESERVATIONS}
        for reservation in MOCK_SCOOTER_RESERVATIONS:
            status_str = reservation["status"]
            if status_str not in all_statuses:
                continue
            all_statuses.discard(status_str)

            with self.subTest(status=status_str):
                status = ReservationStatus(status_str)
                is_cancelled = status == ReservationStatus.CANCELLED
                responses = MockAPIResponses(reservations=[reservation])
                at = self._run_as_admin(responses)
                at.selectbox(key="manage_reservations_id_selection").select_index(0)
                at = self._run_as_admin(responses, at=at, allow_errors=is_cancelled)

                # Confirm is disabled when already terminal or already confirmed
                expect_confirm_disabled = status in {
                    ReservationStatus.CANCELLED,
                    ReservationStatus.COMPLETED,
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.PICKED_UP,
                }
                # Cancel is disabled only for hard-terminal statuses
                expect_cancel_disabled = status in {
                    ReservationStatus.CANCELLED,
                    ReservationStatus.COMPLETED,
                    ReservationStatus.PICKED_UP,
                }
                self.assertEqual(
                    expect_confirm_disabled,
                    at.button(key="confirm_reservation").disabled,
                    f"Confirm disabled state incorrect for {status_str}",
                )
                self.assertEqual(
                    expect_cancel_disabled,
                    at.button(key="cancel_reservation").disabled,
                    f"Cancel disabled state incorrect for {status_str}",
                )

                # Date and device_type are always disabled when an existing reservation is loaded
                self.assertTrue(at.date_input("update_reservation_date").disabled)
                self.assertTrue(at.selectbox("update_reservation_device_type").disabled)

                # Other fields disabled only for terminal statuses
                expect_fields_disabled = status in {
                    ReservationStatus.CANCELLED,
                    ReservationStatus.COMPLETED,
                    ReservationStatus.PICKED_UP,
                }
                self.assertEqual(
                    expect_fields_disabled,
                    at.text_input("update_reservation_name").disabled,
                    f"Name field disabled state incorrect for {status_str}",
                )

    def test_update_passes_correct_reservation_data(self):
        """Updating a reservation passes the modified data to submit_update_reservation_form."""
        responses = MockAPIResponses(reservations=[_EDITABLE_RESERVATION])
        at = self._load_reservations_and_select(responses)
        at.text_input(key="update_reservation_name").set_value("New Name")
        at.button(key="update_reservation_submit").click()
        with patch.object(reservation_utils, "submit_update_reservation_form") as mock_submit:
            self._run_as_admin(responses, at=at)
            mock_submit.assert_called_once()
            _, kwargs = mock_submit.call_args
            self.assertEqual("New Name", kwargs["reservation"]["name"])
            self.assertEqual(_EDITABLE_RESERVATION["id"], kwargs["reservation"]["id"])

    def test_update_with_empty_name_shows_validation_error(self):
        """Clearing the name field and submitting triggers a validation error, not a service call."""
        responses = MockAPIResponses(reservations=[_EDITABLE_RESERVATION])
        at = self._load_reservations_and_select(responses)
        at.text_input("update_reservation_name").set_value("")
        at.button(key="update_reservation_submit").click()
        with patch.object(DataService, "update_reservation") as mock_update, \
                patch.object(utils, "display_validation_errors") as mock_errors:
            self._run_as_admin(responses, at=at, allow_errors=True)
            mock_update.assert_not_called()
            mock_errors.assert_called_once()

    def test_confirm_button_disabled_for_already_confirmed(self):
        """The Confirm button is disabled when the reservation is already in Confirmed status."""
        confirmed = [r for r in MOCK_SCOOTER_RESERVATIONS if r["status"] == "Confirmed"][0]
        responses = MockAPIResponses(reservations=[confirmed])
        at = self._load_reservations_and_select(responses)
        self.assertTrue(
            at.button(key="confirm_reservation").disabled,
            "Confirm should be disabled when reservation is already Confirmed",
        )
