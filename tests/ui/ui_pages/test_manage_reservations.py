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
        data = self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="reservations")
        mock_requests = MockRequests(mock_reservations_data=data)

        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        self.assertEqual(
            "S0830001 - Teresa Austin (10:00 AM, BLC)",
            at.selectbox(key="manage_reservations_id_selection").options[0],
        )

    def test_update_reservation_info(self):
        """Check the UI content for updating reservation information"""
        data = self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="reservations")
        data[0]["date"] = CNEDates.get_default_date().strftime("%Y-%m-%d")  # mock with default date
        mock_requests = MockRequests(mock_reservations_data=data)

        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        at.selectbox(key="manage_reservations_id_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        # check that reservation date and reservation type cannot be modified
        self.assertTrue(at.date_input("reservation_form_date").disabled)
        self.assertTrue(at.selectbox("reservation_form_device_type").disabled)

        # test confirm reservation button
        at.button(key="confirm_reservation").click()
        with patch.object(DataService, attribute="update_reservation_status") as mock_update_reservation_status:
            self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            mock_update_reservation_status.assert_called_once_with(
                reservation_id="S0830001",
                status=ReservationStatus.CONFIRMED,
            )

        # test cancel reservation button
        at.button(key="cancel_reservation").click()
        with patch.object(DataService, attribute="update_reservation_status") as mock_update_reservation_status:
            self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            mock_update_reservation_status.assert_called_once_with(
                reservation_id="S0830001",
                status=ReservationStatus.CANCELLED,
            )
