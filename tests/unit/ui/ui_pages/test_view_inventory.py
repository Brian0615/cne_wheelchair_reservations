import itertools
from unittest.mock import patch

from common.constants import DeviceStatus, DeviceType, Location
from tests.unit.base_tests import BaseTestCases


class TestViewInventory(BaseTestCases.BaseUIPageTest):
    """Class for testing the View Inventory page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/view_inventory.py"

    def test_empty_inventory(self):
        """Check the UI content for when there are no devices in the inventory"""
        with patch("streamlit.plotly_chart") as mock_plotly_chart:
            self._test_empty_inventory(expected_num_warnings=2)
            mock_plotly_chart.assert_not_called()  # charts for device status should not be created

    def test_single_device_inventory_only(self):
        """Check the UI content for when there is only one device type in the inventory"""
        for device_type in DeviceType:
            with patch("streamlit.plotly_chart") as mock_plotly_chart:
                with self.subTest(device_type=device_type.name):
                    self._subtest_single_device_inventory_only(device_type=device_type)
                    mock_plotly_chart.assert_called_once()

    # pylint: disable=duplicate-code
    def test_filter_inventory(self):
        """Check the UI content for filtering the inventory"""
        for device_type, status, location in itertools.product(
                DeviceType,
                [None] + list(DeviceStatus),
                [None] + list(Location),
        ):
            with self.subTest(
                    device_type=device_type.name,
                    status=status.name if status else None,
                    location=location.name if location else None,
            ):
                self._subtest_filter_inventory(device_type=device_type, status=status, location=location)
