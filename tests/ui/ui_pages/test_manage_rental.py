from tests.base_tests import BaseTestCases


class TestManageRental(BaseTestCases.BaseUIPageTest):
    """Class for testing the Manage Rental page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/manage_rental.py"
