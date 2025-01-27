from tests.base_tests import BaseTestCases


class TestHome(BaseTestCases.BaseUIPageTest):

    def setUp(self):
        self.page_path = "ui/ui_pages/home.py"

    # things to test:
    # - if there are no reservations, a warning should be displayed
