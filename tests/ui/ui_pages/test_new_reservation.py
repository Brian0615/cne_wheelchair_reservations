from datetime import datetime, time
from unittest.mock import patch

from common.constants import DeviceType, Location
from common.data_models import NewReservation
from common.utils import get_default_timezone
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests
from ui.src import utils
from ui.src.constants import CNEDates
from ui.src.data_service import DataService


class TestNewReservation(BaseTestCases.BaseUIPageTest):
    """Class for testing the New Reservation page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/new_reservation.py"

    def test_new_reservation_render_form(self):
        """Check the rendering of the new reservation form"""
        mock_requests = MockRequests()
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        self.assertEqual(
            at.button(key="reservation_form_submit_button").label,
            "Submit Reservation"
        )

    def test_new_reservation_submit_form(self):
        """Check the submission of the new reservation form"""
        mock_requests = MockRequests()
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)

        at.selectbox(key="reservation_form_device_type").select(DeviceType.SCOOTER)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        at.selectbox(key="reservation_form_location").select(Location.BLC)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        at.text_input(key="reservation_form_name").set_value("John Doe")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        at.text_input(key="reservation_form_phone_number").set_value("123-456-7890")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        at.time_input(key="reservation_form_reservation_time").set_value(time(11, 30))
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)

        with patch.object(
                DataService,
                attribute="add_new_reservation",
                side_effect=[(200, "MockReservationID")]
        ) as mock_add_new_reservation:
            with patch("streamlit.success") as mock_success:
                at.button(key="reservation_form_submit_button").click()
                self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
                mock_add_new_reservation.assert_called_once_with(
                    reservation=NewReservation(
                        date=CNEDates.get_default_date(),
                        device_type=DeviceType.SCOOTER,
                        location=Location.BLC,
                        name="John Doe",
                        phone_number="123-456-7890",
                        reservation_time=get_default_timezone().localize(
                            datetime.combine(CNEDates.get_default_date(), time(hour=11, minute=30))
                        ),  # check that the time gets converted properly
                        notes=""
                    )
                )
                mock_success.assert_called_once()

    def test_new_reservation_validation_errors(self):
        """Check the submission of the new reservation form with invalidated data"""
        mock_requests = MockRequests()
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        at.button(key="reservation_form_submit_button").click()
        with patch.object(utils, attribute="display_validation_errors") as mock_display_validation_errors:
            self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
            mock_display_validation_errors.assert_called_once()
