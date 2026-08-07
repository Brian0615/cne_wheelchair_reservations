from datetime import date, datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

import api.routers.rentals as rentals_module
from api.routers import rentals_router
from api.src.exceptions import DeviceNotFoundOrInvalidStatusException, RentalNotFoundOrNotEditableException
from common.utils import get_default_timezone


def _make_app():
    app = FastAPI()
    app.include_router(rentals_router)
    return app


def _new_rental_payload():
    tz = get_default_timezone()
    return {
        "cne_year": 2025,
        "date": "2025-08-20",
        "device_id": "W01",
        "device_type": "Wheelchair",
        "reservation_id": None,
        "pickup_location": "BLC",
        "pickup_time": tz.localize(datetime(2025, 8, 20, 11, 0)).isoformat(),
        "status": "In Progress",
        "name": "John Doe",
        "phone_number": "4168202370",
        "address": "123 Test St",
        "city": "Toronto",
        "province": "Ontario",
        "postal_code": "M5G2C3",
        "country": "CAN",
        "fee_payment_amount": 20,
        "fee_payment_method": "Cash",
        "deposit_payment_amount": 50,
        "deposit_payment_method": "Cash",
        "items_left_behind": [],
        "notes": None,
        "staff_name": "Staff One",
        "return_location": None,
        "return_time": None,
        "return_staff_name": None,
    }


@mock_aws
class TestRentalsRouter(TestCase):
    """Integration tests for the /rentals router endpoints."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.patcher = patch.object(rentals_module, "db_service", self.mock_db)
        self.patcher.start()
        self.client = TestClient(_make_app())

    def tearDown(self):
        self.patcher.stop()

    # ── POST /rentals/add ─────────────────────────────────────────────────

    def test_add_new_rental_returns_id(self):
        self.mock_db.insert_rental.return_value = "W0820001"
        response = self.client.post("/rentals/add", json=_new_rental_payload())
        self.assertEqual(200, response.status_code)
        self.assertEqual("W0820001", response.json())

    def test_add_new_rental_device_invalid_returns_400(self):
        self.mock_db.insert_rental.side_effect = DeviceNotFoundOrInvalidStatusException(
            2025, "W01", "Available"
        )
        response = self.client.post("/rentals/add", json=_new_rental_payload())
        self.assertEqual(400, response.status_code)

    # ── POST /rentals/complete_rental ─────────────────────────────────────

    def test_complete_rental_calls_service(self):
        self.mock_db.complete_rental.return_value = None
        tz = get_default_timezone()
        payload = {
            "cne_year": 2025,
            "id": "W0820001",
            "date": "2025-08-20",
            "device_id": "W01",
            "reservation_id": None,
            "name": "John Doe",
            "return_location": "BLC",
            "return_time": tz.localize(datetime(2025, 8, 20, 16, 0)).isoformat(),
            "return_staff_name": "Staff One",
        }
        response = self.client.post("/rentals/complete_rental", json=payload)
        self.assertEqual(200, response.status_code)
        self.mock_db.complete_rental.assert_called_once()

    def test_complete_rental_not_found_returns_400(self):
        self.mock_db.complete_rental.side_effect = RentalNotFoundOrNotEditableException(2025, "W0820001")
        tz = get_default_timezone()
        payload = {
            "cne_year": 2025,
            "id": "W0820001",
            "date": "2025-08-20",
            "device_id": "W01",
            "reservation_id": None,
            "name": "John Doe",
            "return_location": "BLC",
            "return_time": tz.localize(datetime(2025, 8, 20, 16, 0)).isoformat(),
            "return_staff_name": "Staff One",
        }
        response = self.client.post("/rentals/complete_rental", json=payload)
        self.assertEqual(400, response.status_code)

    # ── GET /rentals/get_rentals_on_date ──────────────────────────────────

    def test_get_rentals_on_date_returns_list(self):
        tz = get_default_timezone()
        self.mock_db.get_rentals_on_date.return_value = [
            {
                "cne_year": 2025,
                "id": "W0820001",
                "date": "2025-08-20",
                "device_id": "W01",
                "device_type": "Wheelchair",
                "reservation_id": None,
                "pickup_location": "BLC",
                "pickup_time": tz.localize(datetime(2025, 8, 20, 11, 0)).isoformat(),
                "status": "In Progress",
                "name": "John Doe",
                "phone_number": "+1 416-820-2370",
                "deposit_payment_method": "Cash",
                "deposit_payment_amount": 50,
                "items_left_behind": [],
                "notes": None,
                "return_location": None,
                "return_time": None,
            }
        ]
        response = self.client.get(
            "/rentals/get_rentals_on_date",
            params={"date": "2025-08-20T00:00:00"},
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()))

    def test_get_rentals_on_date_in_progress_only(self):
        self.mock_db.get_rentals_on_date.return_value = []
        response = self.client.get(
            "/rentals/get_rentals_on_date",
            params={"date": "2025-08-20T00:00:00", "in_progress_rentals_only": True},
        )
        self.assertEqual(200, response.status_code)
        self.mock_db.get_rentals_on_date.assert_called_once_with(
            date=date(2025, 8, 20),
            device_type=None,
            in_progress_rentals_only=True,
        )
