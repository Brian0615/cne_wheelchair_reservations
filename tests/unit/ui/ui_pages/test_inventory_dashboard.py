import math
from unittest.mock import patch

import streamlit as st

from tests.unit.base_tests import BaseTestCases
from tests.unit.mock_requests import MockRequests
from common.constants import DeviceType
from ui.src.device_utils import _DASHBOARD_CHART_MAX_ROWS


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
            # 1 column-header trace per location's column (each location wraps every
            # _DASHBOARD_CHART_MAX_ROWS of its own devices) + 2 traces (rectangle + label) per device
            locations = {device["location"] for device in data}
            num_columns = sum(
                math.ceil(sum(1 for device in data if device["location"] == location) / _DASHBOARD_CHART_MAX_ROWS)
                for location in locations
            )
            self.assertEqual(num_columns + 2 * len(data), len(chart_fig.data))

        self.assertTrue(any("No Wheelchairs" in caption.value for caption in at.caption))

    def test_inventory_chart_columns_weighted_by_chart_width_not_raw_count(self):
        """Column widths should be proportional to each chart's rendered width (one column per
        location, wrapping every 10 of that location's devices), not raw device count -- the
        fixtures (11 scooters, 10 wheelchairs) are deliberately close in count but both land in
        the same 2-column total (neither location in either fixture exceeds 10 devices)."""
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
            # both fixtures split across BLC and PG with neither location over 10 devices, so both
            # need exactly 1 column per location (2 total) despite the close overall counts
            self.assertEqual([2, 2], inventory_columns_calls[0].args[0])

    def test_gauge_titles_use_a_larger_font_than_the_home_page(self):
        """The dashboard's gauge titles should use a larger font size than the Home page's default,
        scoped to this page only (see the paired assertion in TestHome)."""
        gauge_figs = self._get_mock_reservations_gauge_figs()
        self.assertGreater(len(gauge_figs), 0, "At least one gauge chart should have rendered")
        for fig in gauge_figs:
            for trace in fig.data:
                self.assertEqual(20, trace.title.font.size)

    def test_gauge_chart_height_is_increased_to_avoid_clipping(self):
        """The dashboard's gauge charts should be taller than the Home page's default, giving the
        larger title font room to render without being clipped, scoped to this page only (see the
        paired assertion in TestHome)."""
        gauge_figs = self._get_mock_reservations_gauge_figs()
        self.assertGreater(len(gauge_figs), 0, "At least one gauge chart should have rendered")
        for fig in gauge_figs:
            self.assertEqual(150, fig.layout.height)

    def test_gauge_captions_use_a_larger_font_than_the_home_page(self):
        """The dashboard's reservation/rental captions should render at a larger font size than the
        Home page's plain st.caption default, scoped to this page only (see the paired assertion in
        TestHome)."""
        at = self._run_with_mock_reservations()

        caption_markdowns = [
            markdown.value for markdown in at.markdown if "Picked Up / Total Reservations" in markdown.value
        ]
        self.assertGreater(len(caption_markdowns), 0, "At least one reservation caption should have rendered")
        for value in caption_markdowns:
            self.assertIn("font-size: 20px", value)

    def test_gauge_badge_tags_use_a_larger_font_than_the_home_page(self):
        """The dashboard's 'BLC/PG Reservations/Rentals' badge tags should render at a larger font
        size than the Home page's plain st.badge default, scoped to this page only (see the paired
        assertion in TestHome). st.badge has no font-size parameter, so this is done by injecting a
        scoped CSS override targeting its stMarkdownBadge class."""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        badge_style_markdowns = [
            markdown.value for markdown in at.markdown if "stMarkdownBadge" in markdown.value
        ]
        self.assertEqual(1, len(badge_style_markdowns), "Exactly one badge font-size override should be injected")
        self.assertIn("font-size: 20px !important", badge_style_markdowns[0])

    def test_legend_present(self):
        """The status legend chart should always be rendered as a Plotly chart."""
        with patch("streamlit.plotly_chart") as mock_plotly_chart:
            self._run_app_test_with_mock_requests(mock_requests=MockRequests())

            # with empty inventory/reservations/rentals, the legend is the only plotly_chart call
            mock_plotly_chart.assert_called_once()
            legend_fig = mock_plotly_chart.call_args.args[0]
            labels = {trace.text for trace in legend_fig.data if trace.mode == "text"}
            self.assertEqual({"Available", "Rented", "Backup", "Out of Service"}, labels)
