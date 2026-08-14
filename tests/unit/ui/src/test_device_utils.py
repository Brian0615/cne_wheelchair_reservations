from unittest import TestCase

import pandas as pd

from common.constants import DeviceStatus, DeviceType
from ui.src.device_utils import (
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

    def test_returns_two_columns_for_small_inventory(self):
        """With <=10 devices total, exactly one BLC/PG column pair is created."""
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
        self.assertEqual(2, fig.layout.xaxis.range[1], "Only one BLC/PG column pair should be needed")

    def test_each_device_occupies_the_column_matching_its_location_on_its_own_row(self):
        """A device's ID should appear in whichever column (BLC or PG) matches its location, with
        each successive device (regardless of location) taking the next row down."""
        inventory = pd.DataFrame([
            {"id": "S01", "status": "Available", "location": "BLC"},
            {"id": "S02", "status": "Available", "location": "BLC"},
            {"id": "S03", "status": "Backup", "location": "PG"},
        ])
        fig = create_dashboard_inventory_chart(inventory)

        s01, s02, s03 = (self._get_rectangle_trace(fig, device_id) for device_id in ("S01", "S02", "S03"))
        self.assertEqual(0, s01.x[0], "S01 (BLC) should be in the first (BLC) column")
        self.assertEqual(0, s02.x[0], "S02 (BLC) should be in the first (BLC) column")
        self.assertEqual(1, s03.x[0], "S03 (PG) should be in the second (PG) column")

        # each device takes the next sequential row, regardless of its location
        self.assertEqual(-2, s01.y[0])
        self.assertEqual(-4, s02.y[0])
        self.assertEqual(-6, s03.y[0])

    def test_wraparound_creates_additional_column_pair_beyond_max_rows(self):
        """More than 10 devices total should wrap into an additional BLC/PG column pair."""
        import plotly.graph_objects as go

        devices = [{"id": f"S{i:02d}", "status": "Available", "location": "BLC"} for i in range(1, 13)]
        inventory = pd.DataFrame(devices)
        fig = create_dashboard_inventory_chart(inventory)
        self.assertIsInstance(fig, go.Figure)
        # 12 devices need 2 blocks of up to 10 rows each -> 2 BLC/PG column pairs = 4 columns, plus the
        # extra 0.6-unit gap inserted between the two blocks
        self.assertAlmostEqual(4.6, fig.layout.xaxis.range[1])
        # 4 column-header traces + 2 traces (rectangle + label) per device
        self.assertEqual(4 + 2 * 12, len(fig.data))

        # the 11th device (index 10) should wrap into the second block's BLC column, offset by the gap
        wrapped_device = self._get_rectangle_trace(fig, "S11")
        self.assertAlmostEqual(2.6, wrapped_device.x[0])
        self.assertEqual(-2, wrapped_device.y[0], "The wrapped block's rows should restart from the top")

        # the second block should start noticeably further right than a plain 2-unit column width would
        # place it, confirming the extra inter-block gap was actually applied
        first_block_device = self._get_rectangle_trace(fig, "S01")
        self.assertGreater(wrapped_device.x[0] - first_block_device.x[0], 2, "Blocks should be visually separated")

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
    def _make_inventory(num_devices: int) -> pd.DataFrame:
        return pd.DataFrame([
            {"id": f"S{i:02d}", "status": "Available", "location": "BLC"} for i in range(num_devices)
        ])

    def test_empty_inventory_weighs_one(self):
        self.assertEqual(1, get_dashboard_chart_column_weight(self._make_inventory(0)))

    def test_up_to_ten_devices_weighs_one(self):
        self.assertEqual(1, get_dashboard_chart_column_weight(self._make_inventory(10)))

    def test_eleven_devices_weighs_two(self):
        """11 devices need a second row-block, so the weight should jump to 2 even though the
        count barely exceeds a single block -- unlike a raw device-count weighting, which would
        give 11 devices almost the same weight as 10."""
        self.assertEqual(2, get_dashboard_chart_column_weight(self._make_inventory(11)))

    def test_twenty_devices_weighs_two(self):
        self.assertEqual(2, get_dashboard_chart_column_weight(self._make_inventory(20)))

    def test_twenty_one_devices_weighs_three(self):
        self.assertEqual(3, get_dashboard_chart_column_weight(self._make_inventory(21)))


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
