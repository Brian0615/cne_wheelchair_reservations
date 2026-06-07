from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

import api.routers.reservations as reservations_module
from api.routers import reservations_router
from api.src.exceptions import NewReservationNotFoundOrNotEditableException, ReservationNotFoundOrNotEditableException
from common.constants import DeviceType, Location, ReservationStatus
from common.utils import get_default_timezone


def _make_app():
    app = FastAPI()
    app.include_router(reservations_router)
    return app


def _new_reservation_payload():
    tz = get_default_timezone()
    return {
        "cne_year": 2025,
        "date": "2025-08-20",
        "device_type": "Scooter",
        "location": "BLC",
        "reservation_time": tz.localize(datetime(2025, 8, 20, 10, 0)).isoformat(),
        "name": "Alice Smith",
        "phone_number": "9052938402",
        "notes": "",
        "status": "Reserved",
        "rental_id": None,
        "id": None,
    }


@mock_aws
class TestReservationsRouter(TestCase):
    """Integration tests for the /reservations router endpoints."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.patcher = patch.object(reservations_module, "db_service", self.mock_db)
        self.patcher.start()
        self.client = TestClient(_make_app())

    def tearDown(self):
        self.patcher.stop()

    # ── GET /reservations/get_reservation_count ───────────────────────────

    def test_get_reservation_count_returns_list(self):
        self.mock_db.get_reservation_count.return_value = pd.DataFrame([
            {"date": "2025-08-20", "device_type": "Scooter", "location": "BLC", "count": 3},
        ])
        response = self.client.get(
            "/reservations/get_reservation_count",
            params={"cne_year": 2025},
        )
        self.assertEqual(200, response.status_code)
        data = response.json()
        self.assertEqual(1, len(data))
        self.assertEqual(3, data[0]["count"])

    # ── GET /reservations/get_reservations_on_date ────────────────────────

    def test_get_reservations_on_date_returns_list(self):
        tz = get_default_timezone()
        self.mock_db.get_reservations_on_date.return_value = [
            {
                "cne_year": 2025,
                "id": "S0820001",
                "date": "2025-08-20",
                "device_type": "Scooter",
                "location": "BLC",
                "reservation_time": tz.localize(datetime(2025, 8, 20, 10, 0)).isoformat(),
                "name": "Alice Smith",
                "phone_number": "+1 905-293-8402",
                "notes": "",
                "status": "Reserved",
                "rental_id": None,
            }
        ]
        response = self.client.get(
            "/reservations/get_reservations_on_date",
            params={"date": "2025-08-20T00:00:00"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()))

    def test_get_reservations_filters_by_device_type(self):
        self.mock_db.get_reservations_on_date.return_value = []
        self.client.get(
            "/reservations/get_reservations_on_date",
            params={"date": "2025-08-20T00:00:00", "device_type": "Scooter"},
        )
        self.mock_db.get_reservations_on_date.assert_called_once_with(
            date=datetime(2025, 8, 20).date(),
            device_type=DeviceType.SCOOTER,
            exclude_picked_up_reservations=False,
        )

    # ── POST /reservations/add ────────────────────────────────────────────

    def test_add_reservation_returns_id(self):
        self.mock_db.insert_reservation.return_value = "S0820001"
        response = self.client.post("/reservations/add", json=_new_reservation_payload())
        self.assertEqual(200, response.status_code)
        self.assertEqual("S0820001", response.json())

    # ── POST /reservations/update_reservation ─────────────────────────────

    def test_update_reservation_calls_service(self):
        self.mock_db.update_reservation.return_value = None
        tz = get_default_timezone()
        payload = {
            "cne_year": 2025,
            "id": "S0820001",
            "date": "2025-08-20",
            "device_type": "Scooter",
            "location": "BLC",
            "reservation_time": tz.localize(datetime(2025, 8, 20, 10, 0)).isoformat(),
            "name": "Alice Smith",
            "phone_number": "9052938402",
            "notes": "",
            "status": "Reserved",
            "rental_id": None,
        }
        response = self.client.post("/reservations/update_reservation", json=payload)
        self.assertEqual(200, response.status_code)
        self.mock_db.update_reservation.assert_called_once()

    def test_update_reservation_not_editable_returns_400(self):
        self.mock_db.update_reservation.side_effect = ReservationNotFoundOrNotEditableException(
            "Reservation not editable"
        )
        tz = get_default_timezone()
        payload = {
            "cne_year": 2025,
            "id": "S0820001",
            "date": "2025-08-20",
            "device_type": "Scooter",
            "location": "BLC",
            "reservation_time": tz.localize(datetime(2025, 8, 20, 10, 0)).isoformat(),
            "name": "Alice Smith",
            "phone_number": "9052938402",
            "notes": "",
            "status": "Reserved",
            "rental_id": None,
        }
        response = self.client.post("/reservations/update_reservation", json=payload)
        self.assertEqual(400, response.status_code)

    # ── POST /reservations/update_reservation_status ──────────────────────

    def test_update_reservation_status_calls_service(self):
        self.mock_db.update_reservation_status.return_value = None
        response = self.client.post(
            "/reservations/update_reservation_status",
            params={
                "cne_year": 2025,
                "reservation_id": "S0820001",
                "reservation_status": "Confirmed",
            },
        )
        self.assertEqual(200, response.status_code)
        self.mock_db.update_reservation_status.assert_called_once_with(
            cne_year=2025,
            reservation_id="S0820001",
            status=ReservationStatus.CONFIRMED,
        )

    def test_update_reservation_status_not_editable_returns_400(self):
        self.mock_db.update_reservation_status.side_effect = NewReservationNotFoundOrNotEditableException(
            2025, "S0820001"
        )
        response = self.client.post(
            "/reservations/update_reservation_status",
            params={
                "cne_year": 2025,
                "reservation_id": "S0820001",
                "reservation_status": "Confirmed",
            },
        )
        self.assertEqual(400, response.status_code)
