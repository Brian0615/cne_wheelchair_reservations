from datetime import date, datetime
from unittest import TestCase

from streamlit.testing.v1 import AppTest

from common.constants import DeviceType, ReservationStatus, Location
from common.data_models import Reservation
from common.utils import get_default_timezone
from ui.src.constants import CNEDates


class TestReservationForm(TestCase):

    def setUp(self):

        self.mock_reservation = Reservation(
            id="S0901001",
            date=date(2025, 9, 1),
            device_type=DeviceType.SCOOTER,
            name="John Doe",
            phone_number="123-456-7890",
            location=Location.BLC,
            reservation_time=get_default_timezone().localize(datetime(2025, 9, 1, 15, 30)),
            status=ReservationStatus.RESERVED,
            notes="Test notes"
        )

    def test_initialize_form_new_reservation(self):

        def run_initialize_form():
            from ui.forms.reservation_form import ReservationForm

            form = ReservationForm(key_prefix="test_form")
            form.initialize_form()

        at = AppTest.from_function(run_initialize_form).run()
        self.assertEqual(at.session_state["test_form_date"], CNEDates.get_default_new_reservation_date())
        self.assertEqual(at.session_state["test_form_device_type"], None)
        self.assertEqual(at.session_state["test_form_location"], None)
        self.assertEqual(at.session_state["test_form_name"], None)
        self.assertEqual(at.session_state["test_form_phone_number"], None)
        self.assertEqual(at.session_state["test_form_time"], CNEDates.get_default_new_reservation_time())
        self.assertEqual(at.session_state["test_form_notes"], None)

    def test_initialize_form_existing_reservation(self):

        def run_initialize_form(reservation):
            from ui.forms.reservation_form import ReservationForm

            form = ReservationForm(key_prefix="test_form", existing_reservation=reservation)
            form.initialize_form()

        at = AppTest.from_function(run_initialize_form, kwargs={"reservation": self.mock_reservation}).run()
        self.assertEqual(at.session_state["test_form_date"], self.mock_reservation.date)
        self.assertEqual(at.session_state["test_form_device_type"], self.mock_reservation.device_type)
        self.assertEqual(at.session_state["test_form_location"], self.mock_reservation.location)
        self.assertEqual(at.session_state["test_form_name"], self.mock_reservation.name)
        self.assertEqual(at.session_state["test_form_phone_number"], self.mock_reservation.phone_number)
        self.assertEqual(at.session_state["test_form_time"], self.mock_reservation.reservation_time)
        self.assertEqual(at.session_state["test_form_notes"], self.mock_reservation.notes)

    def test_render_form_new_reservation(self):

        def run_render_form():
            from ui.forms.reservation_form import ReservationForm

            form = ReservationForm(key_prefix="test_form")
            form.render_form()

        at = AppTest.from_function(run_render_form).run()
        for element_type in [at.button, at.date_input, at.selectbox, at.text_input, at.time_input]:
            for element in element_type:
                self.assertFalse(element.disabled)

        self.assertEqual(at.button("test_form_submit").label, "Submit Reservation")

    def test_render_form_existing_reservation(self):
        """Test rendering the form with an existing reservation"""

        def run_render_form(is_disabled: bool, reservation):
            from ui.forms.reservation_form import ReservationForm

            form = ReservationForm(key_prefix="test_form", existing_reservation=reservation, disabled=is_disabled)
            form.render_form()

        for disabled in [True, False]:
            with self.subTest(f"Render with disabled={disabled}"):
                at = AppTest.from_function(
                    run_render_form,
                    kwargs={"is_disabled": disabled, "reservation": self.mock_reservation}
                ).run()
                for element_type in [at.button, at.date_input, at.selectbox, at.text_input, at.time_input]:
                    for element in element_type:
                        if element.key in ["test_form_date", "test_form_device_type"]:
                            self.assertTrue(element.disabled, "Date and Device Type should always be disabled")
                        else:
                            self.assertEqual(element.disabled, disabled)

                self.assertEqual(at.button("test_form_submit").label, "Update Reservation")
