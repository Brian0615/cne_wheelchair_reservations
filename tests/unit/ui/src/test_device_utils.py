from unittest import TestCase

import pandas as pd

from common.constants import DeviceStatus, DeviceType
from ui.src.device_utils import (
    _DASHBOARD_CHART_COLUMN_GAP,
    _DASHBOARD_CHART_LOCATION_GAP,
    _DASHBOARD_CHART_MAX_ROWS,
    create_dashboard_inventory_chart,
    create_dashboard_legend_chart,
    create_inventory_chart,
    get_dashboard_chart_column_weight,
    get_manage_devices_str,
)


class TestGetManageDevicesStr(TestCase):
    """Tests for get_manage_devices_str."""

    def test_singular_label(self):
        label = get_manage_devices_str(action="add", device_type=DeviceType.SCOOTER, num_devices=1)
        self.assertEqual("Add 1 Scooter", label)

    def test_plural_label(self):
        label = get_manage_devices_str(action="remove", device_type=DeviceType.WHEELCHAIR, num_devices=3)
        self.assertEqual("Remove 3 Wheelchairs", label)

    def test_zero_devices_uses_plural(self):
        label = get_manage_devices_str(action="update", device_type=DeviceType.SCOOTER, num_devices=0)
        self.assertEqual("Update 0 Scooters", label)

    def test_negative_one_uses_singular(self):
        label = get_manage_devices_str(action="transfer", device_type=DeviceType.WHEELCHAIR, num_devices=-1)
        self.assertEqual("Transfer -1 Wheelchair", label)

    def test_action_is_title_cased(self):
        label = get_manage_devices_str(action="add", device_type=DeviceType.SCOOTER, num_devices=2)
        self.assertTrue(label.startswith("Add"), "Action should be title-cased")


class TestCreateInventoryChart(TestCase):
    """Tests for create_inventory_chart."""

    def test_returns_figure_for_non_empty_inventory(self):
        import plotly.graph_objects as go

        inventory = pd.DataFrame([
            {"id": "S01", "status": "Available", "location": "BLC"},
            {"id": "S02", "status": "Rented", "location": "PG"},
        ])
        fig = create_inventory_chart(inventory)
        self.assertIsInstance(fig, go.Figure)
        self.assertGreater(len(fig.data), 0, "Figure should have traces for each device")

    def test_returns_figure_with_correct_trace_count(self):
        """Each device gets two traces (filled rectangle + label text)."""
        import plotly.graph_objects as go

        inventory = pd.DataFrame([
            {"id": "S01", "status": "Available", "location": "BLC"},
        ])
        fig = create_inventory_chart(inventory)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(2, len(fig.data), "Each device should produce exactly 2 traces")


class TestCreateDashboardInventoryChart(TestCase):
    """Tests for create_dashboard_inventory_chart."""

    @staticmethod
    def _get_rectangle_trace(fig, device_id: str):
        for trace in fig.data:
            if trace.mode == "lines" and trace.text and trace.text.startswith(f"<b>{device_id}</b>"):
                return trace
        raise AssertionError(f"No rectangle trace found for device {device_id}")

    @staticmethod
    def _get_label_trace(fig, device_id: str):
        for trace in fig.data:
            if trace.mode == "text" and trace.text == device_id:
                return trace
        raise AssertionError(f"No label trace found for device {device_id}")

    def test_device_labels_use_a_larger_font_than_the_view_inventory_chart(self):
        """The Inventory Dashboard's device labels should be more readable than
        create_inventory_chart's (the View Inventory page), which keeps its original, smaller font."""
        inventory = pd.DataFrame([{"id": "S01", "status": "Available", "location": "BLC"}])
        dashboard_label = self._get_label_trace(create_dashboard_inventory_chart(inventory), "S01")
        view_inventory_label = next(
            trace for trace in create_inventory_chart(inventory).data if trace.mode == "text"
        )
        self.assertGreater(dashboard_label.textfont.size, view_inventory_label.textfont.size)

    def test_column_header_font_matches_device_label_font(self):
        """Column headers should be sized consistently with the device labels below them."""
        inventory = pd.DataFrame([{"id": "S01", "status": "Available", "location": "BLC"}])
        fig = create_dashboard_inventory_chart(inventory)
        header_trace = next(trace for trace in fig.data if trace.mode == "text" and trace.text == "<b>BLC</b>")
        label_trace = self._get_label_trace(fig, "S01")
        self.assertEqual(label_trace.textfont.size, header_trace.textfont.size)

    def test_returns_two_columns_for_small_inventory(self):
        """With <=_DASHBOARD_CHART_MAX_ROWS devices at each location, exactly one column per
        location is created."""
        import plotly.graph_objects as go

        inventory = pd.DataFrame([
            {"id": "S01", "status": "Available", "location": "BLC"},
            {"id": "S02", "status": "Rented", "location": "BLC"},
            {"id": "S03", "status": "Backup", "location": "PG"},
        ])
        fig = create_dashboard_inventory_chart(inventory)
        self.assertIsInstance(fig, go.Figure)
        # 2 column-header traces + 2 traces (rectangle + label) per device
        self.assertEqual(2 + 2 * 3, len(fig.data))
        self.assertAlmostEqual(
            2 + _DASHBOARD_CHART_LOCATION_GAP, fig.layout.xaxis.range[1],
            msg="Only one column per location should be needed",
        )

    def test_each_location_gets_its_own_column_with_devices_stacked_by_row(self):
        """A device's ID should appear in the column for its location, stacked by row within that
        location's own device order -- locations never share rows or columns with each other."""
        inventory = pd.DataFrame([
            {"id": "S01", "status": "Available", "location": "BLC"},
            {"id": "S02", "status": "Available", "location": "BLC"},
            {"id": "S03", "status": "Backup", "location": "PG"},
        ])
        fig = create_dashboard_inventory_chart(inventory)

        s01, s02, s03 = (self._get_rectangle_trace(fig, device_id) for device_id in ("S01", "S02", "S03"))
        self.assertEqual(0, s01.x[0], "S01 (BLC) should be in the first (BLC) column")
        self.assertEqual(0, s02.x[0], "S02 (BLC) should be in the first (BLC) column")
        self.assertAlmostEqual(
            1 + _DASHBOARD_CHART_LOCATION_GAP, s03.x[0], msg="S03 (PG) should be in the second (PG) column"
        )

        # the two BLC devices stack in successive rows within their own column
        self.assertEqual(-2, s01.y[0])
        self.assertEqual(-4, s02.y[0])
        # PG's single device starts back at the top row of its own column, independent of BLC's rows
        self.assertEqual(-2, s03.y[0])

    def test_wraparound_creates_additional_column_within_the_same_location(self):
        """More than _DASHBOARD_CHART_MAX_ROWS devices at one location should wrap into an
        additional column for that same location, without touching the other location's column."""
        import plotly.graph_objects as go

        num_devices = _DASHBOARD_CHART_MAX_ROWS + 1
        devices = [{"id": f"S{i:02d}", "status": "Available", "location": "BLC"} for i in range(1, num_devices + 1)]
        inventory = pd.DataFrame(devices)
        fig = create_dashboard_inventory_chart(inventory)
        self.assertIsInstance(fig, go.Figure)
        # BLC needs 2 wrapped columns (joined by the small same-location gap), PG (empty) still gets
        # its own placeholder column (joined by the larger cross-location gap) -> 3 columns total
        expected_width = 3 + _DASHBOARD_CHART_COLUMN_GAP + _DASHBOARD_CHART_LOCATION_GAP
        self.assertAlmostEqual(expected_width, fig.layout.xaxis.range[1])
        # 3 column-header traces + 2 traces (rectangle + label) per device
        self.assertEqual(3 + 2 * num_devices, len(fig.data))

        # the first device beyond _DASHBOARD_CHART_MAX_ROWS should wrap into BLC's second column,
        # offset by the small same-location gap
        wrapped_device = self._get_rectangle_trace(fig, f"S{num_devices:02d}")
        self.assertAlmostEqual(1 + _DASHBOARD_CHART_COLUMN_GAP, wrapped_device.x[0])
        self.assertEqual(-2, wrapped_device.y[0], "The wrapped column's rows should restart from the top")

        # BLC's second column should still start further right than a plain 1-unit column width
        # would place it, confirming the inter-column gap was actually applied
        first_column_device = self._get_rectangle_trace(fig, "S01")
        self.assertGreater(
            wrapped_device.x[0] - first_column_device.x[0], 1, "Columns should be visually separated"
        )

    def test_gap_within_a_location_is_smaller_than_the_gap_between_locations(self):
        """Wrapped columns belonging to the same location should sit closer together than the gap
        that separates one location's columns from the next."""
        num_devices = _DASHBOARD_CHART_MAX_ROWS + 1
        devices = [{"id": f"S{i:02d}", "status": "Available", "location": "BLC"} for i in range(1, num_devices + 1)]
        devices.append({"id": "P01", "status": "Available", "location": "PG"})
        inventory = pd.DataFrame(devices)
        fig = create_dashboard_inventory_chart(inventory)

        blc_col1 = self._get_rectangle_trace(fig, "S01")
        blc_col2 = self._get_rectangle_trace(fig, f"S{num_devices:02d}")
        pg_col1 = self._get_rectangle_trace(fig, "P01")

        within_location_gap = blc_col2.x[0] - blc_col1.x[0]
        between_location_gap = pg_col1.x[0] - blc_col2.x[0]
        self.assertLess(
            within_location_gap, between_location_gap,
            "BLC's two wrapped columns should sit closer together than the gap to PG's column",
        )

    def test_divider_line_drawn_between_locations(self):
        """A vertical divider should separate BLC's columns from PG's, positioned in the gap
        between the two rather than overlapping either location's cells."""
        inventory = pd.DataFrame([
            {"id": "S01", "status": "Available", "location": "BLC"},
            {"id": "S02", "status": "Backup", "location": "PG"},
        ])
        fig = create_dashboard_inventory_chart(inventory)

        self.assertEqual(1, len(fig.layout.shapes), "Exactly one divider should separate BLC from PG")
        divider = fig.layout.shapes[0]
        self.assertEqual("line", divider.type)

        blc_cell = self._get_rectangle_trace(fig, "S01")
        pg_cell = self._get_rectangle_trace(fig, "S02")
        self.assertGreater(divider.x0, blc_cell.x[2], "Divider should sit to the right of BLC's cell")
        self.assertLess(divider.x0, pg_cell.x[0], "Divider should sit to the left of PG's cell")

    def test_one_location_without_devices_still_gets_its_own_placeholder_column(self):
        """If BLC doesn't fill its last column, PG must still start a new column rather than sharing
        BLC's leftover space -- even when PG has no devices at all."""
        inventory = pd.DataFrame([
            {"id": "S01", "status": "Available", "location": "BLC"},
        ])
        fig = create_dashboard_inventory_chart(inventory)

        s01 = self._get_rectangle_trace(fig, "S01")
        self.assertEqual(0, s01.x[0], "S01 (BLC) should be in the first (BLC) column")
        # 2 column-header traces (one for BLC, one for empty PG) + 2 traces for S01
        self.assertEqual(2 + 2, len(fig.data))

    def test_empty_inventory_still_shows_base_columns(self):
        """An empty inventory should still render the BLC/PG column headers, with no device traces."""
        import plotly.graph_objects as go

        inventory = pd.DataFrame(columns=["id", "status", "location"])
        fig = create_dashboard_inventory_chart(inventory)
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(2, len(fig.data), "Only the 2 column-header traces should be present")


class TestGetDashboardChartColumnWeight(TestCase):
    """Tests for get_dashboard_chart_column_weight."""

    @staticmethod
    def _make_inventory(num_devices: int, location: str = "BLC") -> pd.DataFrame:
        return pd.DataFrame(
            [{"id": f"S{i:02d}", "status": "Available", "location": location} for i in range(num_devices)],
            columns=["id", "status", "location"],
        )

    def test_empty_inventory_weighs_one(self):
        """A totally empty inventory renders no chart at all (just a caption), so it should weigh
        the minimum rather than one placeholder column per location."""
        self.assertEqual(1, get_dashboard_chart_column_weight(self._make_inventory(0)))

    def test_up_to_max_rows_devices_at_one_location_weighs_two(self):
        """The other (empty) location still gets its own placeholder column."""
        self.assertEqual(2, get_dashboard_chart_column_weight(self._make_inventory(_DASHBOARD_CHART_MAX_ROWS)))

    def test_one_over_max_rows_devices_at_one_location_weighs_three(self):
        """One device over _DASHBOARD_CHART_MAX_ROWS needs a second column for that location, so the
        weight should jump even though the count barely exceeds a single column -- unlike a raw
        device-count weighting, which would give it almost the same weight as exactly max_rows."""
        self.assertEqual(
            3, get_dashboard_chart_column_weight(self._make_inventory(_DASHBOARD_CHART_MAX_ROWS + 1))
        )

    def test_two_full_blocks_at_one_location_weighs_three(self):
        self.assertEqual(
            3, get_dashboard_chart_column_weight(self._make_inventory(_DASHBOARD_CHART_MAX_ROWS * 2))
        )

    def test_just_over_two_full_blocks_at_one_location_weighs_four(self):
        self.assertEqual(
            4, get_dashboard_chart_column_weight(self._make_inventory(_DASHBOARD_CHART_MAX_ROWS * 2 + 1))
        )

    def test_devices_split_across_both_locations_sum_each_locations_columns(self):
        """BLC and PG never share a column, so their column counts add rather than combine -- BLC
        needing 2 columns plus PG needing 1 column needs 3 columns total."""
        inventory = pd.concat([
            self._make_inventory(_DASHBOARD_CHART_MAX_ROWS + 1, "BLC"), self._make_inventory(1, "PG")
        ])
        self.assertEqual(3, get_dashboard_chart_column_weight(inventory))


class TestCreateDashboardLegendChart(TestCase):
    """Tests for create_dashboard_legend_chart."""

    def test_returns_figure_with_one_swatch_and_label_per_status(self):
        import plotly.graph_objects as go

        fig = create_dashboard_legend_chart()
        self.assertIsInstance(fig, go.Figure)
        # 2 traces (colour swatch rectangle + label text) per DeviceStatus
        self.assertEqual(2 * len(DeviceStatus), len(fig.data))

    def test_swatch_colours_match_the_inventory_chart_colours(self):
        fig = create_dashboard_legend_chart()
        swatch_traces = [trace for trace in fig.data if trace.mode == "lines"]
        colours = {trace.fillcolor for trace in swatch_traces}
        expected_colours = {DeviceStatus.get_device_status_colour(status) for status in DeviceStatus}
        self.assertEqual(expected_colours, colours)

    def test_label_text_matches_status_values(self):
        fig = create_dashboard_legend_chart()
        label_traces = [trace for trace in fig.data if trace.mode == "text"]
        labels = {trace.text for trace in label_traces}
        self.assertEqual({status.value for status in DeviceStatus}, labels)

    def test_label_font_matches_dashboard_chart_font(self):
        """The legend's labels should match the Inventory Dashboard chart's font size, since the two
        are meant to visually match."""
        legend_label = next(trace for trace in create_dashboard_legend_chart().data if trace.mode == "text")

        inventory = pd.DataFrame([{"id": "S01", "status": "Available", "location": "BLC"}])
        dashboard_fig = create_dashboard_inventory_chart(inventory)
        dashboard_label = next(
            trace for trace in dashboard_fig.data if trace.mode == "text" and trace.text == "S01"
        )
        self.assertEqual(dashboard_label.textfont.size, legend_label.textfont.size)
