from unittest.mock import patch

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
