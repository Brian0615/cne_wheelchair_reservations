from datetime import date

from moto import mock_aws

from api.src.exceptions import ReservationNotFoundOrNotEditableException
from common.constants import DeviceType, Location, ReservationStatus
from common.data_models import Reservation
from tests.unit.base_tests import BaseTestCases


# pylint: disable=missing-class-docstring,missing-function-docstring
@mock_aws
class TestDynamoDBServiceReservations(BaseTestCases.BaseDynamoDBServiceTest):

    def test_get_reservations_on_date(self):
        response = self.service.get_reservations_on_date(date=date(2025, 8, 20))
        self.assertEqual(len(response), 0)

        reservation = self._generate_mock_new_reservation()
        reservation.id = self.service.insert_reservation(reservation=reservation)
        response = self.service.get_reservations_on_date(date=date(2025, 8, 20))
        self.assertEqual(len(response), 1)
        self.assertEqual([Reservation(**reservation.model_dump())], [Reservation(**x) for x in response])
        response = self.service.get_reservations_on_date(date=date(2025, 8, 20),device_type=DeviceType.SCOOTER)
        self.assertEqual(len(response), 1)
        response = self.service.get_reservations_on_date(date=date(2025, 8, 20),device_type=DeviceType.WHEELCHAIR)
        self.assertEqual(len(response), 0)

        reservation = self._generate_mock_new_reservation(
            overrides={"status": ReservationStatus.PICKED_UP, "rental_id": "S0820010"}
        )
        reservation.id = self.service.insert_reservation(reservation=reservation)
        response = self.service.get_reservations_on_date(date=date(2025, 8, 20))
        self.assertEqual(len(response), 2)
        response = self.service.get_reservations_on_date(date=date(2025, 8, 20), exclude_picked_up_reservations=True)
        self.assertEqual(len(response), 1)
        response = self.service.get_reservations_on_date(date=date(2025, 8, 21))
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

    def test_update_reservation(self):
        reservation = self._generate_mock_reservation(overrides={"cne_year": 2025, "id": "S0820001"})
        with self.assertRaises(
                ReservationNotFoundOrNotEditableException,
                msg="Exception should be raised if reservation does not exist",
        ):
            self.service.update_reservation(reservation=reservation)

        reservation = self._generate_mock_new_reservation()
        self.service.insert_reservation(reservation=reservation)
        reservation = self.service.get_reservations_on_date(date=date(2025, 8, 20))[0]
        reservation["name"] = reservation["name"] + " New"
        reservation["status"] = ReservationStatus.COMPLETED
        self.service.update_reservation(reservation=Reservation(**reservation))

        response = self.service.get_reservations_on_date(date=date(2025, 8, 20))
        self.assertEqual(len(response), 1)
        self.assertEqual([Reservation(**reservation)], [Reservation(**x) for x in response])

        reservation = self.service.get_reservations_on_date(date=date(2025, 8, 20))[0]
        reservation["name"] = reservation["name"] + " New2"
        with self.assertRaises(
                ReservationNotFoundOrNotEditableException,
                msg="Exception should be raised if reservation is un-editable (as it is already picked up)",
        ):
            self.service.update_reservation(reservation=Reservation(**reservation))


    def test_update_reservation_status(self):
        with self.assertRaises(
                ReservationNotFoundOrNotEditableException,
                msg="Exception should be raised if reservation does not exist",
        ):
            self.service.update_reservation_status(
                cne_year=2025,
                reservation_id="S0820001",
                status=ReservationStatus.PICKED_UP,
            )

        reservation = self._generate_mock_new_reservation()
        self.service.insert_reservation(reservation=reservation)
        self.service.update_reservation_status(
            cne_year=2025,
            reservation_id="S0820001",
            status=ReservationStatus.PICKED_UP,
        )
        response = self.service.get_reservations_on_date(date=date(2025, 8, 20))
        self.assertEqual(ReservationStatus(response[0]["status"]), ReservationStatus.PICKED_UP)

        with self.assertRaises(
                ReservationNotFoundOrNotEditableException,
                msg="Exception should be raised if reservation is un-editable (as it is already picked up)",
        ):
            self.service.update_reservation_status(
                cne_year=2025,
                reservation_id="S0820001",
                status=ReservationStatus.CANCELLED,
            )
