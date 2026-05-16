from datetime import date, datetime
from unittest import TestCase

from streamlit.testing.v1 import AppTest

from common.constants import DeviceType, ReservationStatus, Location
from common.data_models import Reservation
from common.utils import get_default_timezone
from ui.src.constants import CNEDates


class TestReservationForm(TestCase):
    """Test the reservation form"""

    def setUp(self):
        curr_year = datetime.now().year

        # pylint: disable=duplicate-code
        self.mock_reservation = Reservation(
            cne_year=curr_year,
            id="S0901001",
            date=date(curr_year, 9, 1),
            device_type=DeviceType.SCOOTER,
            name="John Doe",
            phone_number="+1 437-293-0384",
            location=Location.BLC,
            reservation_time=get_default_timezone().localize(datetime(curr_year, 9, 1, 15, 30)),
            status=ReservationStatus.RESERVED,
            notes="Test notes"
        )

    # pylint: disable=import-outside-toplevel
    @staticmethod
    def _run_form(reservation, render: bool, disabled: bool = False):
        """Run the form rendering"""
        from ui.forms.reservation_form import ReservationForm

        form = ReservationForm(key_prefix="test_form", existing_reservation=reservation, disabled=disabled)
        form.initialize_form()
        if render:
            form.render_form()

    def test_initialize_form_new_reservation(self):
        """Test that the form is initialized with the correct default values"""

        at = AppTest.from_function(self._run_form, args=(None, False)).run()
        self.assertEqual(at.session_state["test_form_date"], CNEDates.get_default_new_reservation_date())
        self.assertEqual(at.session_state["test_form_device_type"], None)
        self.assertEqual(at.session_state["test_form_location"], None)
        self.assertEqual(at.session_state["test_form_name"], None)
        self.assertEqual(at.session_state["test_form_phone_number"], None)
        self.assertEqual(at.session_state["test_form_time"], CNEDates.get_default_new_reservation_time())
        self.assertEqual(at.session_state["test_form_notes"], None)

    def test_initialize_form_existing_reservation(self):
        """Test that the form is initialized with the correct values for an existing reservation"""

        at = AppTest.from_function(self._run_form, args=(self.mock_reservation, False)).run()
        self.assertEqual(at.session_state["test_form_date"], self.mock_reservation.date)
        self.assertEqual(at.session_state["test_form_device_type"], self.mock_reservation.device_type)
        self.assertEqual(at.session_state["test_form_location"], self.mock_reservation.location)
        self.assertEqual(at.session_state["test_form_name"], self.mock_reservation.name)
        self.assertEqual(
            at.session_state["test_form_phone_number"],
            self.mock_reservation.phone_number.replace("tel:", ""),  # pylint: disable=no-member
        )
        self.assertEqual(at.session_state["test_form_time"], self.mock_reservation.reservation_time)
        self.assertEqual(at.session_state["test_form_notes"], self.mock_reservation.notes)

    def test_render_form_new_reservation(self):
        """Test rendering the form with a new reservation"""

        at = AppTest.from_function(self._run_form, args=(None, True)).run()

        # Check all form elements are rendered
        form_elements_found = {
            "buttons": len(at.button),
            "date_inputs": len(at.date_input),
            "selectboxes": len(at.selectbox),
            "text_inputs": len(at.text_input),
            "time_inputs": len(at.time_input),
        }

        # Verify all elements exist
        for element_type in [at.button, at.date_input, at.selectbox, at.text_input, at.time_input]:
            for element in element_type:
                self.assertFalse(element.disabled,
                                 f"Element {getattr(element, 'key', 'unknown')} should not be disabled")

        # Find the submit button by label
        submit_button = None
        button_labels = [button.label for button in at.button]
        for button in at.button:
            if button.label == "Submit Reservation":
                submit_button = button
                break
        self.assertIsNotNone(
            submit_button,
            f"Submit button not found. Form elements: {form_elements_found}. "
            f"Button labels: {button_labels}"
        )
        self.assertEqual(submit_button.label, "Submit Reservation")

    def test_render_form_existing_reservation(self):
        """Test rendering the form with an existing reservation"""

        for disabled in [True, False]:
            with self.subTest(f"Render with disabled={disabled}"):
                at = AppTest.from_function(
                    self._run_form,
                    kwargs={"render": True, "reservation": self.mock_reservation, "disabled": disabled}
                ).run()

                # Check what elements are rendered
                form_elements_found = {
                    "buttons": len(at.button),
                    "date_inputs": len(at.date_input),
                    "selectboxes": len(at.selectbox),
                    "text_inputs": len(at.text_input),
                    "time_inputs": len(at.time_input),
                }

                for element_type in [at.date_input, at.selectbox, at.text_input, at.time_input]:
                    for element in element_type:
                        if element.key in ["test_form_date", "test_form_device_type"]:
                            self.assertTrue(element.disabled, "Date and Device Type should always be disabled")
                        else:
                            self.assertEqual(element.disabled, disabled)

                # Check buttons
                for button in at.button:
                    # Buttons should have the same disabled state as other_fields_disabled
                    # which is: self.disabled and self.existing_reservation is not None
                    button_expected_disabled = disabled and self.mock_reservation is not None
                    self.assertEqual(
                        button.disabled,
                        button_expected_disabled,
                        f"Button disabled state should be {button_expected_disabled}, got {button.disabled}",
                    )

                # Find the update button by label
                update_button = None
                button_labels = [button.label for button in at.button]
                for button in at.button:
                    if button.label == "Update Reservation":
                        update_button = button
                        break
                self.assertIsNotNone(
                    update_button,
                    f"Update button not found. Form elements: {form_elements_found}. Button labels: {button_labels}"
                )
                self.assertEqual(update_button.label, "Update Reservation")
