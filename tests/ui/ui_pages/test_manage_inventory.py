import itertools

from common.constants import DeviceStatus, DeviceType, Location
from tests.base_tests import BaseTestCases


class TestManageInventory(BaseTestCases.BaseUIPageTest):
    """Class for testing the Manage Inventory page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/manage_inventory.py"

    def test_empty_inventory(self):
        """Check the UI content for when there are no devices in the inventory"""
        self._test_empty_inventory(expected_num_warnings=1)

    def test_single_device_inventory_only(self):
        """Check the UI content for when there is only one device type in the inventory"""
        for device_type in DeviceType:
            with self.subTest(device_type=device_type.name):
                self._subtest_single_device_inventory_only(device_type=device_type)

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
