from datetime import datetime, time
from unittest.mock import patch

from common.constants import DeviceType, Location, ReservationStatus
from common.data_models import NewReservation
from common.utils import get_default_timezone
from tests.unit.base_tests import BaseTestCases
from tests.unit.mock_requests import MockRequests
from ui.src import utils
from ui.src.constants import CNEDates
from ui.src.data_service import DataService


class TestNewReservation(BaseTestCases.BaseUIPageTest):
    """Class for testing the New Reservation page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/new_reservation.py"

    def test_new_reservation_submit_form(self):
        """Check the submission of the new reservation form"""
        mock_requests = MockRequests()
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

        # check that all fields are enabled
        self.assertFalse(at.date_input(key="new_reservation_date").disabled)
        self.assertFalse(at.selectbox(key="new_reservation_device_type").disabled)
        self.assertFalse(at.selectbox(key="new_reservation_location").disabled)
        self.assertFalse(at.text_input(key="new_reservation_name").disabled)
        self.assertFalse(at.text_input(key="new_reservation_phone_number").disabled)
        self.assertFalse(at.time_input(key="new_reservation_time").disabled)
        self.assertFalse(at.text_input(key="new_reservation_notes").disabled)
        self.assertFalse(at.button(key="new_reservation_submit").disabled)

        at.selectbox(key="new_reservation_device_type").select(DeviceType.SCOOTER)
        at.selectbox(key="new_reservation_location").select(Location.BLC)
        at.text_input(key="new_reservation_name").set_value("John Doe")
        at.text_input(key="new_reservation_phone_number").set_value("416-937-2830")
        at.time_input(key="new_reservation_time").set_value(time(11, 30))

        with patch.object(
                DataService,
                attribute="add_new_reservation",
                side_effect=[(200, "MockReservationID")]
        ) as mock_add_new_reservation:
            with patch("streamlit.success") as mock_success:
                at.button(key="new_reservation_submit").click()
                self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
                mock_add_new_reservation.assert_called_once_with(
                    reservation=NewReservation(
                        cne_year=CNEDates.get_cne_year(),
                        date=CNEDates.get_default_new_reservation_date(),
                        device_type=DeviceType.SCOOTER,
                        location=Location.BLC,
                        name="John Doe",
                        phone_number="416-937-2830",
                        reservation_time=get_default_timezone().localize(
                            datetime.combine(CNEDates.get_default_new_reservation_date(), time(hour=11, minute=30))
                        ),  # check that the time gets converted properly
                        notes=None,
                        status=ReservationStatus.PENDING,
                    )
                )
                mock_success.assert_called_once()

    def test_new_reservation_validation_errors(self):
        """Check the submission of the new reservation form with invalidated data"""
        mock_requests = MockRequests()
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        at.button(key="new_reservation_submit").click()
        with patch.object(DataService, attribute="add_new_reservation") as mock_add_new_reservation:
            with patch.object(utils, attribute="display_validation_errors") as mock_display_validation_errors:
                self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at, allow_errors=True)
                mock_add_new_reservation.assert_not_called()
                mock_display_validation_errors.assert_called_once()
