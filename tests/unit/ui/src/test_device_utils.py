from unittest import TestCase

import pandas as pd

from common.constants import DeviceType
from ui.src.device_utils import get_manage_devices_str, create_inventory_chart


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
