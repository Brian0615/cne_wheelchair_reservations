from datetime import date

from moto import mock_aws

from api.src.exceptions import NewDeviceNotFoundException, NewReservationNotFoundOrNotEditableException
from common.constants import DeviceStatus, DeviceType, Location
from common.data_models import Rental, NewDevice
from tests.base_tests import BaseTestCases


# pylint: disable=missing-class-docstring,missing-function-docstring
@mock_aws
class TestDynamoDBServiceRentals(BaseTestCases.BaseDynamoDBServiceTest):

    def test_get_rentals_on_date(self):
        response = self.service.get_rentals_on_date(date=date(2025, 8, 20))
        self.assertEqual(len(response), 0)

        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE)
        ])
        rental = self._generate_mock_new_rental(overrides={"reservation_id": None})
        self.service.insert_rental(rental=rental)
        response = self.service.get_rentals_on_date(date=date(2025, 8, 20))
        self.assertEqual(len(response), 1)
        response = self.service.get_rentals_on_date(date=date(2025, 8, 20), device_type=DeviceType.SCOOTER)
        self.assertEqual(len(response), 0)
        response = self.service.get_rentals_on_date(date=date(2025, 8, 20), device_type=DeviceType.WHEELCHAIR)
        self.assertEqual(len(response), 1)


    def test_insert_rental_walk_in(self):
        rental = self._generate_mock_new_rental(overrides={"reservation_id": None})
        with self.assertRaises(
                NewDeviceNotFoundException,
                msg="Exception should be raised if rental specifies a non-existent device",
        ):
            self.service.insert_rental(rental=rental)

        # inserting a device of the wrong type, error should still be raised
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        with self.assertRaises(
                NewDeviceNotFoundException,
                msg="Exception should still be raised here as the device available is the wrong type",
        ):
            self.service.insert_rental(rental=rental)

        # add the correct device first, insert rental should now be successful
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        self.service.insert_rental(rental=rental)
        responses = self.rentals_table.scan()
        self.assertEqual(len(responses["Items"]), 1)
        self.assertEqual([Rental(**x) for x in responses["Items"]], [Rental(**rental.model_dump(mode="json"))])

        with self.assertRaises(
                NewDeviceNotFoundException,
                msg="Exception should be raised if rental specifies an unavailable device",
        ):
            self.service.insert_rental(rental=rental)

    def test_insert_rental_reserved(self):
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        rental = self._generate_mock_new_rental()
        with self.assertRaises(
                NewReservationNotFoundOrNotEditableException,
                msg="Exception should be raised if rental specifies a non-existent reservation",
        ):
            self.service.insert_rental(rental)

        reservation = self._generate_mock_new_reservation(overrides={"device_type": DeviceType.WHEELCHAIR})
        reservation.id = self.service.insert_reservation(reservation=reservation)
        self.service.insert_rental(rental=rental)
        responses = self.rentals_table.scan()
        self.assertEqual(responses["Items"][0]["id"], "W0820001")
        self.assertEqual(responses["Items"][0]["reservation_id"], "W0820001")

        # starting a rental on an already-started reservation should raise an error
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        rental = self._generate_mock_new_rental(overrides={"device_id": "W02"})
        with self.assertRaises(
                NewReservationNotFoundOrNotEditableException,
                msg="Exception should be raised if rental specifies a non-editable reservation",
        ):
            self.service.insert_rental(rental=rental)
