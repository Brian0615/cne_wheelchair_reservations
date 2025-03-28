from unittest.mock import patch

from common.constants import DeviceType, ReservationStatus
from common.data_models import Reservation
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests
from ui.src import reservation_utils, utils
from ui.src.constants import CNEDates
from ui.src.data_service import DataService


class TestManageReservations(BaseTestCases.BaseUIPageTest):
    """Class for testing the Manage Reservations page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/manage_reservations.py"

    def _init_app_test_with_loaded_reservations(self):
        data = self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="reservations")
        for element in data:
            element["date"] = CNEDates.get_default_date().strftime("%Y-%m-%d")  # mock with default date
        mock_requests = MockRequests(mock_reservations_data=data)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        return mock_requests, at

    def test_no_reservations(self):
        """Check the UI content for when there are no reservations"""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        today_date = CNEDates.get_default_date().strftime("%b %d, %Y")
        self.assertTrue(
            any("No Reservations" in warning.value and today_date in warning.value for warning in at.warning),
            "A warning message should be displayed that there are no reservations"
        )
        self.assertEqual(0, len(at.selectbox), "Drop-down should not be displayed if there are no reservations")

    def test_reservation_selection_formatting(self):
        """Check that the reservations are formatted correctly in the drop-down menu"""
        _, at = self._init_app_test_with_loaded_reservations()
        self.assertEqual(
            "S0830001 - Teresa Austin (10:00 AM, BLC)",
            at.selectbox(key="manage_reservations_id_selection").options[0],
        )

    def test_confirm_reservation_button(self):
        """Check that the Confirm Reservation button updates reservation status"""
        mock_requests, at = self._init_app_test_with_loaded_reservations()
        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        # test that reservation status was updated with confirm reservation button
        at.button(key="confirm_reservation").click()
        with patch.object(DataService, attribute="update_reservation_status") as mock_update_status:
            self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            mock_update_status.assert_called_once_with(
                reservation_id="S0830001",
                status=ReservationStatus.CONFIRMED,
            )

    def test_cancel_reservation_button(self):
        """Check the Cancel Reservation button updates reservation status"""
        mock_requests, at = self._init_app_test_with_loaded_reservations()
        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        # test that reservation status was updated with confirm reservation button
        at.button(key="cancel_reservation").click()
        with patch.object(DataService, attribute="update_reservation_status") as mock_update_status:
            self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            mock_update_status.assert_called_once_with(
                reservation_id="S0830001",
                status=ReservationStatus.CANCELLED,
            )

    def test_field_states(self):
        """Check whether fields are enabled/disabled appropriately"""
        mock_requests, at = self._init_app_test_with_loaded_reservations()

        checked_statuses = set()
        for i, reservation in enumerate(mock_requests.mock_reservations_data):
            if reservation["status"] in checked_statuses:
                continue
            with self.subTest(msg=f"Checking field states for a {reservation['status']} reservation"):
                at.selectbox(key="manage_reservations_id_selection").select_index(i)
                reservation_status = ReservationStatus(reservation["status"])
                at = self._run_app_test_with_mock_requests(
                    mock_requests=mock_requests,
                    at=at,
                    allow_errors=reservation_status == ReservationStatus.CANCELLED
                )

                # check that Confirm/Cancel buttons are disabled/enabled appropriately
                self.assertEqual(
                    at.button(key="confirm_reservation").disabled,
                    reservation_status in {
                        ReservationStatus.CANCELLED,
                        ReservationStatus.COMPLETED,
                        ReservationStatus.CONFIRMED,
                        ReservationStatus.PICKED_UP,
                    },
                    msg="Confirm Reservation button should be disabled if reservation "
                        "is cancelled/completed/confirmed/picked up"
                )
                self.assertEqual(
                    at.button(key="cancel_reservation").disabled,
                    reservation_status in {
                        ReservationStatus.CANCELLED,
                        ReservationStatus.COMPLETED,
                        ReservationStatus.PICKED_UP,
                    },
                    msg="Cancel Reservation button should be disabled if reservation "
                        "is cancelled/completed/picked up"
                )

                # check that form fields are disabled/enabled appropriately
                self.assertTrue(at.date_input("update_reservation_date").disabled)
                self.assertTrue(at.selectbox("update_reservation_device_type").disabled)
                self.assertEqual(
                    at.text_input("update_reservation_name").disabled,
                    ReservationStatus(reservation["status"]) in {
                        ReservationStatus.CANCELLED,
                        ReservationStatus.COMPLETED,
                        ReservationStatus.PICKED_UP,
                    }
                )
            checked_statuses.add(reservation["status"])

    def test_switch_selected_reservation(self):
        """Check that the reservation information updates when a different reservation is selected"""
        mock_requests, at = self._init_app_test_with_loaded_reservations()

        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        self.assertEqual(at.text_input("update_reservation_name").value, "Teresa Austin")
        self.assertEqual(at.time_input("update_reservation_time").proto.value, "10:00")

        at.selectbox(key="manage_reservations_id_selection").select_index(1)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        self.assertEqual(at.text_input("update_reservation_name").value, "Denise Mccarty")
        self.assertEqual(at.time_input("update_reservation_time").proto.value, "13:35")

    def test_submit_update_reservation_form(self):
        """Check that the Update Reservation button submits the form"""
        mock_requests, at = self._init_app_test_with_loaded_reservations()

        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        at.text_input("update_reservation_name").set_value("New Name")
        at.button(key="update_reservation_submit").click()
        with patch.object(reservation_utils, attribute="submit_update_reservation_form") as mock_submit_form:
            self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            expected_reservation_data = Reservation(**mock_requests.mock_reservations_data[0]).model_dump()
            expected_reservation_data["name"] = "New Name"
            expected_reservation_data["reservation_time"] = expected_reservation_data["reservation_time"].time()
            expected_reservation_data.pop("rental_id")
            mock_submit_form.assert_called_once_with(reservation=expected_reservation_data)

    def test_submit_update_reservation_validation_errors(self):
        """Check that validation errors are displayed when the form is submitted with invalid data"""
        mock_requests, at = self._init_app_test_with_loaded_reservations()

        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        at.text_input("update_reservation_name").set_value("")
        at.button(key="update_reservation_submit").click()
        with patch.object(DataService, attribute="update_reservation") as mock_update_reservation:
            with patch.object(utils, attribute="display_validation_errors") as mock_display_errors:
                self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at, allow_errors=True)
                mock_update_reservation.assert_not_called()
                mock_display_errors.assert_called_once()
