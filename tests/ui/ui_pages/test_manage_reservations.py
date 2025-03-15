from unittest.mock import patch

from common.constants import DeviceType, ReservationStatus
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests
from ui.src.constants import CNEDates
from ui.src.data_service import DataService


class TestManageReservations(BaseTestCases.BaseUIPageTest):
    """Class for testing the Manage Reservations page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/manage_reservations.py"

    def _init_app_test_with_scooter_reservations(self):
        data = self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="reservations")
        for i in range(len(data)):
            data[i]["date"] = CNEDates.get_default_date().strftime("%Y-%m-%d")  # mock with default date
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
        _, at = self._init_app_test_with_scooter_reservations()
        self.assertEqual(
            "S0830001 - Teresa Austin (10:00 AM, BLC)",
            at.selectbox(key="manage_reservations_id_selection").options[0],
        )

    def test_enabled_confirm_reservation_button(self):
        """Check the Confirm Reservation button"""
        mock_requests, at = self._init_app_test_with_scooter_reservations()
        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        # check that the confirm reservation button is enabled
        self.assertFalse(
            at.button(key="confirm_reservation").disabled,
            msg="Confirm Reservation button should be enabled"
        )

        # test that reservation status was updated with confirm reservation button
        at.button(key="confirm_reservation").click()
        with patch.object(DataService, attribute="update_reservation_status") as mock_update_status:
            self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            mock_update_status.assert_called_once_with(
                reservation_id="S0830001",
                status=ReservationStatus.CONFIRMED,
            )

    def test_disabled_confirm_reservation_button(self):
        """Check that the Confirm Reservation button is disabled for a cancelled/confirmed/picked up reservation"""
        mock_requests, at = self._init_app_test_with_scooter_reservations()

        for i, reservation in enumerate(mock_requests.mock_reservations_data):
            if ReservationStatus(reservation["status"]) not in {ReservationStatus.PENDING, ReservationStatus.RESERVED}:
                with self.subTest(msg=f"Checking Confirm Reservation button for a {reservation['status']} reservation"):
                    at.selectbox(key="manage_reservations_id_selection").select_index(i)
                    at = self._run_app_test_with_mock_requests(
                        mock_requests=mock_requests,
                        at=at,
                        allow_errors=ReservationStatus(reservation["status"]) == ReservationStatus.CANCELLED,
                    )

                    # check that the confirm reservation button is disabled
                    self.assertTrue(
                        at.button(key="confirm_reservation").disabled,
                        msg="Confirm Reservation button should be disabled unless reservation is pending confirmation"
                    )

    def test_enabled_cancel_reservation_button(self):
        """Check the Cancel Reservation button when it should be enabled"""
        mock_requests, at = self._init_app_test_with_scooter_reservations()

        for i, reservation in enumerate(mock_requests.mock_reservations_data):
            if ReservationStatus(reservation["status"]) not in {
                ReservationStatus.CANCELLED,
                ReservationStatus.PICKED_UP,
                ReservationStatus.COMPLETED
            }:
                with self.subTest(msg=f"Checking Cancel Reservation button for a {reservation['status']} reservation"):
                    at.selectbox(key="manage_reservations_id_selection").select_index(i)
                    at = self._run_app_test_with_mock_requests(mock_requests=mock_requests,at=at,)

                    # check that the confirm reservation button is disabled
                    self.assertFalse(
                        at.button(key="cancel_reservation").disabled,
                        msg="Cancel Reservation button should be enabled unless reservation "
                            "is cancelled/completed/picked up"
                    )

                    # test that reservation status was updated with cancel reservation button
                    at.button(key="cancel_reservation").click()
                    with patch.object(DataService, attribute="update_reservation_status") as mock_update_status:
                        self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
                        mock_update_status.assert_called_once_with(
                            reservation_id=reservation["id"],
                            status=ReservationStatus.CANCELLED,
                        )


    def test_disabled_cancel_reservation_button(self):
        """Check the Cancel Reservation button when it should be disabled"""
        mock_requests, at = self._init_app_test_with_scooter_reservations()

        for i, reservation in enumerate(mock_requests.mock_reservations_data):
            if ReservationStatus(reservation["status"]) in {
                ReservationStatus.CANCELLED,
                ReservationStatus.PICKED_UP,
                ReservationStatus.COMPLETED
            }:
                with self.subTest(msg=f"Checking Cancel Reservation button for a {reservation['status']} reservation"):
                    at.selectbox(key="manage_reservations_id_selection").select_index(i)
                    at = self._run_app_test_with_mock_requests(
                        mock_requests=mock_requests,
                        at=at,
                        allow_errors=ReservationStatus(reservation["status"]) == ReservationStatus.CANCELLED,
                    )

                    # check that the confirm reservation button is disabled
                    self.assertTrue(
                        at.button(key="cancel_reservation").disabled,
                        msg="Cancel Reservation button should be disabled if reservation "
                            "is cancelled/completed/picked up"
                    )

    def test_update_reservation_info(self):
        """Check the UI content for updating reservation information"""
        data = self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="reservations")
        data[0]["date"] = CNEDates.get_default_date().strftime("%Y-%m-%d")  # mock with default date
        mock_requests = MockRequests(mock_reservations_data=data)

        # select one of the fake reservations
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        # check that reservation date and reservation type cannot be modified in the update reservation form
        self.assertTrue(
            at.date_input("update_reservation_date").disabled,
            msg="Reservation date should be disabled if updating an existing reservation",
        )
        self.assertTrue(
            at.selectbox("update_reservation_device_type").disabled,
            msg="Reservation type should be disabled if updating an existing reservation",
        )

    def test_switch_selected_reservation(self):
        """Check that the reservation information updates when a different reservation is selected"""
        mock_requests, at = self._init_app_test_with_scooter_reservations()

        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        self.assertEqual(at.text_input("update_reservation_name").value, "Teresa Austin")

        at.selectbox(key="manage_reservations_id_selection").select_index(1)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        self.assertEqual(at.text_input("update_reservation_name").value, "Denise Mccarty")
