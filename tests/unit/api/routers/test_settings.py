from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

import api.routers.settings as settings_module
from api.routers import settings_router


def _make_app():
    app = FastAPI()
    app.include_router(settings_router)
    return app


@mock_aws
class TestSettingsRouter(TestCase):
    """Integration tests for the /settings router endpoints."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.patcher = patch.object(settings_module, "db_service", self.mock_db)
        self.patcher.start()
        self.client = TestClient(_make_app())

    def tearDown(self):
        self.patcher.stop()

    # ── GET /settings/get ─────────────────────────────────────────────────

    def test_get_setting_returns_value(self):
        self.mock_db.get_setting.return_value = 100
        response = self.client.get(
            "/settings/get",
            params={"cne_year": 2025, "setting_id": "wheelchair_limit"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(100, response.json())
        self.mock_db.get_setting.assert_called_once_with(cne_year=2025, setting_id="wheelchair_limit")

    def test_get_setting_returns_none_when_not_set(self):
        self.mock_db.get_setting.return_value = None
        response = self.client.get(
            "/settings/get",
            params={"cne_year": 2025, "setting_id": "nonexistent"},
        )
        self.assertEqual(200, response.status_code)
        self.assertIsNone(response.json())

    # ── PUT /settings/update ──────────────────────────────────────────────

    def test_update_setting_calls_service(self):
        self.mock_db.update_settings.return_value = None
        response = self.client.put(
            "/settings/update",
            params={"cne_year": 2025},
            json={"wheelchair_limit": 50},
        )
        self.assertEqual(200, response.status_code)
        self.mock_db.update_settings.assert_called_once_with(
            cne_year=2025, settings={"wheelchair_limit": 50}
        )

    def test_update_multiple_settings(self):
        self.mock_db.update_settings.return_value = None
        response = self.client.put(
            "/settings/update",
            params={"cne_year": 2025},
            json={"wheelchair_limit": 30, "scooter_limit": 20},
        )
        self.assertEqual(200, response.status_code)
        self.mock_db.update_settings.assert_called_once_with(
            cne_year=2025, settings={"wheelchair_limit": 30, "scooter_limit": 20}
        )
