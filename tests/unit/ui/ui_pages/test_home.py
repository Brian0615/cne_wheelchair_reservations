from tests.unit.base_tests import BaseTestCases


class TestHome(BaseTestCases.BaseUIPageTest):
    """Class for testing the Home page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/home.py"
