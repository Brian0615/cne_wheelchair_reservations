from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from common.constants import DeviceType, ReservationStatus, Location
from common.data_models import NewReservation, Reservation
from common.utils import get_default_timezone
from ui.src import reservation_utils
from ui.src.data_service import DataService
from ui.forms.reservation_form import ReservationForm


# pylint: disable=import-outside-toplevel
class TestReservationUtils(TestCase):
    """Test the reservation utils"""

    # pylint: disable=duplicate-code
    def setUp(self):
        self.mock_reservation = Reservation(
            cne_year=2025,
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

    @staticmethod
    def _run_submit_new_reservation_form(reservation):
        """Run the submit new reservation form function"""
        from ui.src.reservation_utils import submit_new_reservation_form

        submit_new_reservation_form(reservation=reservation)

    @staticmethod
    def _run_submit_update_reservation_form(reservation):
        """Run the submit update reservation form function"""
        from ui.src.reservation_utils import submit_update_reservation_form

        submit_update_reservation_form(reservation=reservation)

    def test_display_success_dialog(self):
        """Test displaying the success dialog"""

        def run_display_success_dialog(reservation_id, reservation, is_update):
            """Run the display success dialog function"""
            from ui.src.reservation_utils import display_success_dialog

            display_success_dialog(reservation_id=reservation_id, reservation=reservation, is_update=is_update)

        for update in [True, False]:
            at = AppTest.from_function(
                run_display_success_dialog,
                args=(self.mock_reservation.id, self.mock_reservation, update)
            ).run()
            self.assertTrue(
                "updated" if update else "created" in at.success[0].value,
                msg=f"Success dialog should indicate reservation was {'updated' if update else 'created'}"
            )
            self.assertTrue("S0901001" in at.success[0].value, "Success dialog should display reservation ID")

            at.button[0].click()
            with patch("streamlit.rerun") as mock_rerun:
                at.run()
                mock_rerun.assert_called_once()

    def test_submit_new_reservation_form_success(self):
        """Test submitting a new reservation form successfully"""

        with patch.object(
                DataService,
                attribute="add_new_reservation",
                return_value=(200, "S0901001")
        ) as mock_add_new_reservation:
            with patch.object(reservation_utils, "display_success_dialog") as mock_display_success_dialog:
                with patch.object(ReservationForm, "clear_form") as mock_clear_form:
                    reservation_dict = self.mock_reservation.model_dump()
                    reservation_dict["reservation_time"] = reservation_dict["reservation_time"].time()
                    at = AppTest.from_function(self._run_submit_new_reservation_form, args=(reservation_dict,)).run()

                    mock_add_new_reservation.assert_called_once_with(reservation=NewReservation(**reservation_dict))
                    self.assertIsNone(at.session_state["new_reservation_form_errors"])
                    mock_display_success_dialog.assert_called_once_with(
                        reservation_id="S0901001",
                        reservation=NewReservation(**reservation_dict),
                        is_update=False,
                    )
                    mock_clear_form.assert_called_once()

    def test_submit_new_reservation_form_validation_failure(self):
        """Test submitting a new reservation form with validation errors"""

        with patch.object(
                DataService,
                attribute="add_new_reservation",
                return_value=(200, "S0901001")
        ) as mock_add_new_reservation:
            with patch("streamlit.rerun"):  # patch rerun to prevent repeatedly running function
                reservation_dict = self.mock_reservation.model_dump()
                reservation_dict["reservation_time"] = reservation_dict["reservation_time"].time()
                reservation_dict.pop("name")  # drop a field to trigger validation error
                at = AppTest.from_function(self._run_submit_new_reservation_form, args=(reservation_dict,)).run()

                mock_add_new_reservation.assert_not_called()
                self.assertIsNotNone(at.session_state["new_reservation_form_errors"])

    def test_submit_update_reservation_form_success(self):
        """Test submitting an update reservation form successfully"""

        with patch.object(
                DataService,
                attribute="update_reservation",
                return_value=200,
        ) as mock_update_reservation:
            with patch.object(reservation_utils, "display_success_dialog") as mock_display_success_dialog:
                with patch.object(ReservationForm, "clear_form") as mock_clear_form:
                    reservation_dict = self.mock_reservation.model_dump()
                    reservation_dict["reservation_time"] = reservation_dict["reservation_time"].time()
                    at = AppTest.from_function(self._run_submit_update_reservation_form, args=(reservation_dict,)).run()

                    mock_update_reservation.assert_called_once_with(reservation=Reservation(**reservation_dict))
                    self.assertIsNone(at.session_state["update_reservation_form_errors"])
                    mock_display_success_dialog.assert_called_once_with(
                        reservation_id="S0901001",
                        reservation=Reservation(**reservation_dict),
                        is_update=True,
                    )
                    mock_clear_form.assert_called_once()

    def test_submit_update_reservation_form_validation_failure(self):
        """Test submitting an update reservation form with validation errors"""

        with patch.object(
                DataService,
                attribute="update_reservation",
                return_value=200,
        ) as mock_update_reservation:
            with patch("streamlit.rerun"):  # patch rerun to prevent repeatedly running function
                reservation_dict = self.mock_reservation.model_dump()
                reservation_dict["reservation_time"] = reservation_dict["reservation_time"].time()
                reservation_dict.pop("name")
                at = AppTest.from_function(self._run_submit_update_reservation_form, args=(reservation_dict,)).run()

                mock_update_reservation.assert_not_called()
                self.assertIsNotNone(at.session_state["update_reservation_form_errors"])
