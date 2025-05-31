from unittest.mock import patch

from common.constants import DeviceType
from tests.base_tests import BaseTestCases
from tests.mock_requests import MockRequests
from ui.src.data_service import DataService


class TestManageRental(BaseTestCases.BaseUIPageTest):
    """Class for testing the Manage Rental page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/manage_rental.py"

    def _run_manage_rental_with_rental_and_location_filled(self, mock_requests: MockRequests):
        """Run the Manage Rental page with a rental and location filled"""
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests)
        at.selectbox(key="manage_rental_rental_selection").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        at.selectbox(key="change_device_location").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        return at

    def test_no_available_devices(self):
        """Test the UI content for when there are no available devices"""
        mock_requests = MockRequests(
            mock_rentals_data=self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="rentals"),
            mock_inventory_data=[],
        )
        at = self._run_manage_rental_with_rental_and_location_filled(mock_requests=mock_requests)
        self.assertTrue(
            "No Available Devices" in at.warning[0].value,
            msg="A warning should be displayed if there are no available devices"
        )
        self.assertEqual(len(at.button), 0, "Submit button should not be displayed if there are no available devices")

    def test_cache_clear_after_form_submission(self):
        """Test that the rentals list refreshes after a change"""
        mock_requests = MockRequests(
            mock_rentals_data=self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="rentals"),
            mock_inventory_data=self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="inventory"),
        )
        at = self._run_manage_rental_with_rental_and_location_filled(mock_requests=mock_requests)
        at.selectbox(key="change_device_new_device_id").select_index(0)
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        at.text_input(key="change_device_staff_name").set_value("Test Staff")
        at = self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
        at.button(key="change_device_submit_button").click()

        with patch.object(DataService, "get_rentals_on_date") as mock_get_rentals_on_date:
            with patch.object(DataService, "get_available_device_ids") as mock_get_available_device_ids:
                self._run_app_test_with_mock_requests(mock_requests=mock_requests, at=at)
                mock_get_rentals_on_date.clear.assert_called_once()
                mock_get_available_device_ids.clear.assert_called_once()
