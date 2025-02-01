from tests.base_tests import BaseTestCases


class TestManageInventory(BaseTestCases.BaseUIPageTest):
    """Class for testing the Manage Inventory page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/manage_inventory.py"
