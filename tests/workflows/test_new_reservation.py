from datetime import time
from unittest.mock import patch

from common.constants import DeviceType, Location, ReservationStatus
from common.data_models import NewReservation
from common.utils import get_default_timezone
from datetime import datetime
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses
from ui.src import reservation_utils, utils
from common.cne_dates import CNEDates
from ui.src.data_service import DataService


class NewReservationWorkflowTests(WorkflowTestCase):
    """Workflow tests for the New Reservation page."""

    page_path = "ui/ui_pages/new_reservation.py"

    def _run_as_admin(self, responses, at=None, allow_errors=False):
        return self._run(responses, at=at, allow_errors=allow_errors, roles=["admin"])

    def test_form_renders_with_date_and_device_type(self):
        """The reservation form renders with a date input and device type selector on load."""
        at = self._run_as_admin(MockAPIResponses())
        date_inputs = [d for d in at.date_input if "new_reservation_date" in d.key]
        self.assertGreater(len(date_inputs), 0, "Reservation date input should be present")
        device_type_boxes = [s for s in at.selectbox if "new_reservation_device_type" in s.key]
        self.assertGreater(len(device_type_boxes), 0, "Device type selectbox should be present")

    def test_availability_info_shown_after_date_and_type_selected(self):
        """After selecting a date and device type, availability info is displayed."""
        at = self._run_as_admin(MockAPIResponses())
        at.selectbox(key="new_reservation_device_type").select("Scooter")
        at = self._run_as_admin(MockAPIResponses(), at=at)
        # Either a warning (no availability) or info (spots available) should be shown
        has_availability_message = (
                any("No Available Reservations" in w.value for w in at.warning)
                or any("Reservations Available" in i.value for i in at.info)
        )
        self.assertTrue(has_availability_message, "Availability status should be shown after device type selected")

    def test_submit_creates_reservation(self):
        """Filling all required fields and submitting calls the reservation creation function."""
        at = self._run_as_admin(MockAPIResponses())
        at.selectbox(key="new_reservation_device_type").select("Scooter")
        at.selectbox(key="new_reservation_location").select("BLC")
        at.text_input(key="new_reservation_name").set_value("Test User")
        at.text_input(key="new_reservation_phone_number").set_value("9052938402")
        at.button(key="new_reservation_submit").click()
        with patch.object(reservation_utils, "submit_new_reservation_form") as mock_submit:
            at = self._run_as_admin(MockAPIResponses(), at=at)
            mock_submit.assert_called_once()

    def test_all_form_fields_enabled_on_load(self):
        """All reservation form fields are enabled when the page first loads."""
        at = self._run_as_admin(MockAPIResponses())
        self.assertFalse(at.date_input(key="new_reservation_date").disabled)
        self.assertFalse(at.selectbox(key="new_reservation_device_type").disabled)
        self.assertFalse(at.selectbox(key="new_reservation_location").disabled)
        self.assertFalse(at.text_input(key="new_reservation_name").disabled)
        self.assertFalse(at.text_input(key="new_reservation_phone_number").disabled)
        self.assertFalse(at.time_input(key="new_reservation_time").disabled)
        self.assertFalse(at.text_input(key="new_reservation_notes").disabled)
        self.assertFalse(at.button(key="new_reservation_submit").disabled)

    def test_submit_passes_correct_reservation_data(self):
        """Submitting the form calls DataService.add_new_reservation with the expected NewReservation object."""
        mock_requests = MockAPIResponses()
        at = self._run_as_admin(mock_requests)
        at.selectbox(key="new_reservation_device_type").select(DeviceType.SCOOTER)
        at.selectbox(key="new_reservation_location").select(Location.BLC)
        at.text_input(key="new_reservation_name").set_value("John Doe")
        at.text_input(key="new_reservation_phone_number").set_value("416-937-2830")
        at.time_input(key="new_reservation_time").set_value(time(11, 30))

        with patch.object(DataService, "add_new_reservation", return_value=(200, "MockID")) as mock_add:
            at.button(key="new_reservation_submit").click()
            self._run_as_admin(mock_requests, at=at)
            mock_add.assert_called_once_with(
                reservation=NewReservation(
                    cne_year=CNEDates.get_cne_year(),
                    date=CNEDates.get_default_new_reservation_date(),
                    device_type=DeviceType.SCOOTER,
                    location=Location.BLC,
                    name="John Doe",
                    phone_number="416-937-2830",
                    reservation_time=get_default_timezone().localize(
                        datetime.combine(CNEDates.get_default_new_reservation_date(), time(11, 30))
                    ),
                    notes=None,
                    status=ReservationStatus.PENDING,
                )
            )

    def test_submit_with_empty_name_shows_validation_error(self):
        """Submitting the form without a name triggers a validation error, not a service call."""
        mock_requests = MockAPIResponses()
        at = self._run_as_admin(mock_requests)
        at.button(key="new_reservation_submit").click()
        with patch.object(DataService, "add_new_reservation") as mock_add, \
                patch.object(utils, "display_validation_errors") as mock_errors:
            self._run_as_admin(mock_requests, at=at, allow_errors=True)
            mock_add.assert_not_called()
            mock_errors.assert_called_once()

    def test_over_capacity_submit_is_waitlisted(self):
        """When existing reservations meet the limit, submitting creates a waitlisted reservation.

        Uses reservation_limit=5 and reservation_count=5 so num_available=0 without
        triggering the division-by-zero bug that occurs when limit=0.
        """
        responses = MockAPIResponses(reservation_limit=5, reservation_count=5)
        at = self._run_as_admin(responses)
        at.selectbox(key="new_reservation_device_type").select("Scooter")
        at.selectbox(key="new_reservation_location").select("BLC")
        at.text_input(key="new_reservation_name").set_value("Test User")
        at.text_input(key="new_reservation_phone_number").set_value("9052938402")
        at = self._run_as_admin(responses, at=at)
        self.assertTrue(
            any("No Available Reservations" in w.value for w in at.warning),
            "Expected 'No Available Reservations' warning when reservations are at capacity",
        )
        at.button(key="new_reservation_submit").click()
        with patch.object(reservation_utils, "submit_new_reservation_form") as mock_submit:
            at = self._run_as_admin(responses, at=at)
            mock_submit.assert_called_once()
            _, kwargs = mock_submit.call_args
            self.assertTrue(kwargs.get("is_waitlisted"), "Reservation should be waitlisted when at capacity")
