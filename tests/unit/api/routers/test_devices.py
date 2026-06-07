from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

import api.routers.devices as devices_module
from api.routers import devices_router
from api.src.exceptions import DeviceNotFoundException, DeviceNotFoundOrInvalidStatusException
from common.constants import DeviceStatus, DeviceType, Location
from common.data_models import NewDevice


def _make_app():
    app = FastAPI()
    app.include_router(devices_router)
    return app


@mock_aws
class TestDevicesRouter(TestCase):
    """Integration tests for the /devices router endpoints."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.patcher = patch.object(devices_module, "db_service", self.mock_db)
        self.patcher.start()
        self.client = TestClient(_make_app())

    def tearDown(self):
        self.patcher.stop()

    # ── GET /devices/get_available_devices ──────────────────────────────────

    def test_get_available_devices_returns_ids(self):
        self.mock_db.get_available_device_ids.return_value = ["S01", "S02"]
        response = self.client.get(
            "/devices/get_available_devices",
            params={"cne_year": 2025, "device_type": "Scooter", "location": "BLC"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(["S01", "S02"], response.json())

    def test_get_available_devices_without_location(self):
        self.mock_db.get_available_device_ids.return_value = ["W01"]
        response = self.client.get(
            "/devices/get_available_devices",
            params={"cne_year": 2025, "device_type": "Wheelchair"},
        )
        self.assertEqual(200, response.status_code)
        self.mock_db.get_available_device_ids.assert_called_once_with(
            cne_year=2025, device_type=DeviceType.WHEELCHAIR, location=None
        )

    # ── GET /devices/get_full_inventory ────────────────────────────────────

    def test_get_full_inventory_returns_devices(self):
        self.mock_db.get_full_inventory.return_value = [
            {"cne_year": 2025, "id": "S01", "type": "Scooter", "status": "Available", "location": "BLC"},
        ]
        response = self.client.get("/devices/get_full_inventory", params={"cne_year": 2025})
        self.assertEqual(200, response.status_code)
        data = response.json()
        self.assertEqual(1, len(data))
        self.assertEqual("S01", data[0]["id"])

    # ── POST /devices/add ──────────────────────────────────────────────────

    def test_add_devices_calls_service(self):
        self.mock_db.add_devices.return_value = None
        payload = [{"cne_year": 2025, "type": "Scooter", "status": "Available", "location": "BLC"}]
        response = self.client.post("/devices/add", json=payload)
        self.assertEqual(200, response.status_code)
        self.mock_db.add_devices.assert_called_once()

    # ── POST /devices/remove ───────────────────────────────────────────────

    def test_remove_devices_calls_service(self):
        self.mock_db.remove_devices.return_value = None
        response = self.client.post(
            "/devices/remove",
            params={"cne_year": 2025},
            json=["S01", "S02"],
        )
        self.assertEqual(200, response.status_code)
        self.mock_db.remove_devices.assert_called_once_with(cne_year=2025, device_ids=["S01", "S02"])

    def test_remove_devices_not_found_returns_404(self):
        self.mock_db.remove_devices.side_effect = DeviceNotFoundException("Device not found")
        response = self.client.post(
            "/devices/remove",
            params={"cne_year": 2025},
            json=["X99"],
        )
        self.assertEqual(422, response.status_code)

    # ── POST /devices/update_location ─────────────────────────────────────

    def test_update_location_calls_service(self):
        self.mock_db.update_devices_location.return_value = None
        response = self.client.post(
            "/devices/update_location",
            params={"cne_year": 2025, "location": "PG"},
            json=["S01"],
        )
        self.assertEqual(200, response.status_code)
        self.mock_db.update_devices_location.assert_called_once_with(
            cne_year=2025, device_ids=["S01"], location=Location.PG
        )

    def test_update_location_invalid_device_returns_400(self):
        self.mock_db.update_devices_location.side_effect = DeviceNotFoundOrInvalidStatusException(
            2025, "S99", "Available"
        )
        response = self.client.post(
            "/devices/update_location",
            params={"cne_year": 2025, "location": "BLC"},
            json=["S01"],
        )
        self.assertEqual(400, response.status_code)

    # ── POST /devices/update_status ────────────────────────────────────────

    def test_update_status_calls_service(self):
        self.mock_db.update_devices_status.return_value = None
        response = self.client.post(
            "/devices/update_status",
            params={"cne_year": 2025, "status": "Backup"},
            json=["W01"],
        )
        self.assertEqual(200, response.status_code)
        self.mock_db.update_devices_status.assert_called_once_with(
            cne_year=2025, device_ids=["W01"], status=DeviceStatus.BACKUP
        )
