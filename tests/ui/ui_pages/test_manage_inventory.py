from common.constants import DeviceType
from tests.base_tests import BaseTestCases


class TestManageInventory(BaseTestCases.BaseUIPageTest):
    """Class for testing the Manage Inventory page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/manage_inventory.py"

    def test_empty_inventory(self):
        """Check the UI content for when there are no devices in the inventory"""
        self._test_empty_inventory(expected_num_warnings=1)

    def test_scooters_only(self):
        """Check the UI content for when there are only scooters in the inventory"""
        self._test_single_device_inventory_only(device_type=DeviceType.SCOOTER)

    def test_wheelchairs_only(self):
        """Check the UI content for when there are only wheelchairs in the inventory"""
        self._test_single_device_inventory_only(device_type=DeviceType.WHEELCHAIR)
