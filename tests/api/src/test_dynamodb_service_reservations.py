from datetime import date, datetime
from typing import Optional

from moto import mock_aws

from common.constants import DeviceType, Location, ReservationStatus
from common.data_models import NewReservation, Reservation
from common.utils import get_default_timezone
from tests.base_tests import BaseTestCases


# pylint: disable=missing-class-docstring,missing-function-docstring
@mock_aws
class TestDynamoDBServiceReservations(BaseTestCases.BaseDynamoDBServiceTest):

    @staticmethod
    def _generate_mock_new_reservation(overrides: Optional[dict] = None):
        reservation_params = {
            "cne_year": 2025,
            "date": date(2025, 8, 20),
            "device_type": DeviceType.SCOOTER,
            "location": Location.BLC,
            "reservation_time": get_default_timezone().localize(datetime(2025, 8, 20, 11, 30)),
            "name": "Test Name",
            "phone_number": "1234567890",
            "notes": "",
            "status": ReservationStatus.PENDING,
        }
        if overrides:
            for key, value in overrides.items():
                reservation_params[key] = value
        return NewReservation(**reservation_params)

    def test_get_reservations_on_date(self):
        response = self.service.get_reservations_on_date(cne_year=2025, date=date(2025, 8, 20))
        self.assertEqual(len(response), 0)

        reservation = self._generate_mock_new_reservation()
        reservation.id = self.service.insert_reservation(reservation=reservation)
        response = self.service.get_reservations_on_date(cne_year=2025, date=date(2025, 8, 20))
        self.assertEqual(len(response), 1)
        self.assertEqual([Reservation(**reservation.model_dump())], [Reservation(**x) for x in response])
        response = self.service.get_reservations_on_date(
            cne_year=2025,
            date=date(2025, 8, 20),
            device_type=DeviceType.SCOOTER,
        )
        self.assertEqual(len(response), 1)
        response = self.service.get_reservations_on_date(
            cne_year=2025,
            date=date(2025, 8, 20),
            device_type=DeviceType.WHEELCHAIR,
        )
        self.assertEqual(len(response), 0)

        reservation = self._generate_mock_new_reservation(
            overrides={"status": ReservationStatus.PICKED_UP, "rental_id": "S0820010"}
        )
        reservation.id = self.service.insert_reservation(reservation=reservation)
        response = self.service.get_reservations_on_date(cne_year=2025, date=date(2025, 8, 20))
        self.assertEqual(len(response), 2)
        response = self.service.get_reservations_on_date(
            cne_year=2025,
            date=date(2025, 8, 20),
            exclude_picked_up_reservations=True,
        )
        self.assertEqual(len(response), 1)
        response = self.service.get_reservations_on_date(cne_year=2025, date=date(2025, 8, 21))
        self.assertEqual(len(response), 0)

    def test_insert_reservation(self):
        reservation = self._generate_mock_new_reservation()
        response = self.service.insert_reservation(reservation=reservation)
        self.assertEqual(response, "S0820001")

        reservation = self._generate_mock_new_reservation(overrides={"location": Location.PG})
        response = self.service.insert_reservation(reservation=reservation)
        self.assertEqual(response, "S0820002")

        reservation = self._generate_mock_new_reservation(overrides={"cne_year": 2026})
        response = self.service.insert_reservation(reservation=reservation)
        self.assertEqual(response, "S0820001")

        reservation = self._generate_mock_new_reservation(overrides={"device_type": DeviceType.WHEELCHAIR})
        response = self.service.insert_reservation(reservation=reservation)
        self.assertEqual(response, "W0820001")

        reservation = self._generate_mock_new_reservation(overrides={"date": date(2025, 8, 21)})
        response = self.service.insert_reservation(reservation=reservation)
        self.assertEqual(response, "S0821001")
