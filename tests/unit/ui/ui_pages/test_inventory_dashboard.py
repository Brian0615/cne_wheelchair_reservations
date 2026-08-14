import math
from unittest.mock import patch

import streamlit as st

from tests.unit.base_tests import BaseTestCases
from tests.unit.mock_requests import MockRequests
from common.constants import DeviceType


class TestInventoryDashboard(BaseTestCases.BaseUIPageTest):
    """Class for testing the Inventory Dashboard page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/inventory_dashboard.py"

    def test_no_header_is_shown(self):
        """The old 'Inventory Dashboard' page header should no longer be rendered."""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())
        self.assertEqual(0, len(at.header))

    def test_reservation_and_rental_gauge_cards_present(self):
        """The same BLC/PG reservation and rental gauge cards from the Home page should be shown."""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        values = [markdown.value for markdown in at.markdown]
        for label in [":orange-badge[BLC Reservations]", ":violet-badge[PG Reservations]",
                      ":orange-badge[BLC Rentals]", ":violet-badge[PG Rentals]"]:
            self.assertIn(label, values, f"Gauge card should include the {label} badge")

    def test_empty_inventory_shows_captions(self):
        """No devices in inventory: both columns should show a 'No devices in inventory' caption."""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        self.assertTrue(any("No Scooters" in caption.value for caption in at.caption))
        self.assertTrue(any("No Wheelchairs" in caption.value for caption in at.caption))

    def test_devices_render_as_dashboard_chart(self):
        """Devices in inventory should render as a colour-coded dashboard chart."""
        data = self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="inventory")
        with patch("streamlit.plotly_chart") as mock_plotly_chart:
            at = self._run_app_test_with_mock_requests(mock_requests=MockRequests(mock_inventory_data=data))

            # with no reservations/rentals mocked, the gauge cards show warnings instead of charts, so
            # the only plotly_chart calls are the Scooter inventory chart and the legend (in that order)
            self.assertEqual(2, mock_plotly_chart.call_count)
            chart_fig = mock_plotly_chart.call_args_list[0].args[0]
            # 2 column-header traces per block of up to 10 devices + 2 traces (rectangle + label) per device
            num_blocks = math.ceil(len(data) / 10)
            self.assertEqual(2 * num_blocks + 2 * len(data), len(chart_fig.data))

        self.assertTrue(any("No Wheelchairs" in caption.value for caption in at.caption))

    def test_inventory_chart_columns_weighted_by_chart_width_not_raw_count(self):
        """Column widths should be proportional to each chart's rendered width (row-blocks of up
        to 10 devices), not raw device count -- the fixtures (11 scooters, 10 wheelchairs) are
        deliberately close in count but land in different block counts (2 vs 1)."""
        scooter_data = self._load_mock_data_from_json(device_type=DeviceType.SCOOTER, data_type="inventory")
        wheelchair_data = self._load_mock_data_from_json(device_type=DeviceType.WHEELCHAIR, data_type="inventory")
        self.assertEqual(11, len(scooter_data))
        self.assertEqual(10, len(wheelchair_data))

        with patch("streamlit.columns", wraps=st.columns) as mock_columns:
            self._run_app_test_with_mock_requests(
                mock_requests=MockRequests(mock_inventory_data=scooter_data + wheelchair_data)
            )

            # find the st.columns call used for the two inventory charts (a 2-element weight list)
            inventory_columns_calls = [
                call for call in mock_columns.call_args_list
                if call.args and isinstance(call.args[0], list) and len(call.args[0]) == 2
            ]
            self.assertEqual(1, len(inventory_columns_calls))
            # 11 scooters need 2 row-blocks, 10 wheelchairs need only 1, despite the close counts
            self.assertEqual([2, 1], inventory_columns_calls[0].args[0])

    def test_legend_present(self):
        """The status legend chart should always be rendered as a Plotly chart."""
        with patch("streamlit.plotly_chart") as mock_plotly_chart:
            self._run_app_test_with_mock_requests(mock_requests=MockRequests())

            # with empty inventory/reservations/rentals, the legend is the only plotly_chart call
            mock_plotly_chart.assert_called_once()
            legend_fig = mock_plotly_chart.call_args.args[0]
            labels = {trace.text for trace in legend_fig.data if trace.mode == "text"}
            self.assertEqual({"Available", "Rented", "Backup", "Out of Service"}, labels)
