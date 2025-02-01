from tests.base_tests import BaseTestCases


class TestViewInventory(BaseTestCases.BaseUIPageTest):
    """Class for testing the View Inventory page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/view_inventory.py"
