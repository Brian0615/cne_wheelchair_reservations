from datetime import date

from moto import mock_aws

from api.src.exceptions import (
    NewDeviceNotFoundException,
    NewReservationNotFoundOrNotEditableException,
)
from common.constants import DeviceStatus, DeviceType, Location, RentalStatus, ReservationStatus
from common.data_models import Rental, NewDevice
from tests.base_tests import BaseTestCases


# pylint: disable=missing-class-docstring,missing-function-docstring
@mock_aws
class TestDynamoDBServiceRentals(BaseTestCases.BaseDynamoDBServiceTest):

    def _setup_in_progress_rental(self):
        # set up a normal rental
        reservation = self._generate_mock_new_reservation(overrides={"device_type": DeviceType.WHEELCHAIR})
        reservation.id = self.service.insert_reservation(reservation=reservation)
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        rental = self._generate_mock_new_rental(overrides={"reservation_id": reservation.id})
        self.service.insert_rental(rental=rental)
        self.assertEqual(self.service.rentals_table.scan()["Items"][0]["status"], RentalStatus.IN_PROGRESS)
        self.assertEqual(self.service.reservations_table.scan()["Items"][0]["status"], ReservationStatus.PICKED_UP)
        self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], DeviceStatus.RENTED)

    def test_complete_rentals_device(self):
        """Test the complete rentals function if there is an issue with the referenced device"""
        self._setup_in_progress_rental()

        # mock complete rental input
        completed_rental = self._generate_mock_completed_rental(overrides={"reservation_id": "W0820001"})

        # change the device to the wrong status
        for status in DeviceStatus:
            if status == DeviceStatus.RENTED:
                continue
            with self.subTest(status=status.name):
                self.service.update_devices_status(cne_year=2025, device_ids=["W01"], status=status)
                with self.assertRaises(
                    NewDeviceNotFoundException,
                    msg="Exception should be raised if rental specifies a device in the wrong status",
                ):
                    self.service.complete_rental(rental=completed_rental)
                self.assertEqual(self.service.rentals_table.scan()["Items"][0]["status"], RentalStatus.IN_PROGRESS)
                self.assertEqual(
                    self.service.reservations_table.scan()["Items"][0]["status"],
                    ReservationStatus.PICKED_UP,
                )
                self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], status)

        # delete the device
        self.service.remove_devices(cne_year=2025, device_ids=["W01"])
        with self.assertRaises(
            NewDeviceNotFoundException,
            msg="Exception should be raised if rental specifies a non-existent device",
        ):
            self.service.complete_rental(rental=completed_rental)
        self.assertEqual(self.service.rentals_table.scan()["Items"][0]["status"], RentalStatus.IN_PROGRESS)
        self.assertEqual(self.service.reservations_table.scan()["Items"][0]["status"], ReservationStatus.PICKED_UP)
        self.assertEqual(len(self.service.devices_table.scan()["Items"]), 0)

        # re-add the device with the correct status
        self.service.add_devices(
            devices=[
                NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.RENTED)
            ]
        )
        self.service.complete_rental(rental=completed_rental)
        self.assertEqual(self.service.rentals_table.scan()["Items"][0]["status"], RentalStatus.COMPLETED)
        self.assertEqual(self.service.reservations_table.scan()["Items"][0]["status"], ReservationStatus.COMPLETED)
        self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], DeviceStatus.AVAILABLE)

    def test_complete_rentals_reservation(self):
        self._setup_in_progress_rental()

        # mock complete rental input
        completed_rental = self._generate_mock_completed_rental(overrides={"reservation_id": "W0820001"})

        # change the reservation to the wrong status
        for status in ReservationStatus:
            if status == ReservationStatus.PICKED_UP:
                continue
            with self.subTest(status=status.name):
                # force update status without using the service, as the reservation should not be editable
                self.service.reservations_table.update_item(
                    Key={"cne_year": 2025, "id": "W0820001"},
                    UpdateExpression="SET #status = :status",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={":status": status},
                )
                # self.service.update_reservation_status(cne_year=2025, reservation_id="W0820001", status=status)
                with self.assertRaises(
                    NewReservationNotFoundOrNotEditableException,
                    msg="Exception should be raised if rental specifies a reservation in the wrong status",
                ):
                    self.service.complete_rental(rental=completed_rental)
                self.assertEqual(self.service.rentals_table.scan()["Items"][0]["status"], RentalStatus.IN_PROGRESS)
                self.assertEqual(self.service.reservations_table.scan()["Items"][0]["status"], status)
                self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], DeviceStatus.RENTED)

        # change the reservation to the correct status
        self.service.reservations_table.update_item(
            Key={"cne_year": 2025, "id": "W0820001"},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": ReservationStatus.PICKED_UP},
        )
        self.service.complete_rental(rental=completed_rental)
        self.assertEqual(self.service.rentals_table.scan()["Items"][0]["status"], RentalStatus.COMPLETED)
        self.assertEqual(self.service.reservations_table.scan()["Items"][0]["status"], ReservationStatus.COMPLETED)
        self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], DeviceStatus.AVAILABLE)

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
        self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], DeviceStatus.AVAILABLE)

        # add the correct device first, insert rental should now be successful
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        self.service.insert_rental(rental=rental)
        responses = self.service.rentals_table.scan()
        self.assertEqual(len(responses["Items"]), 1)
        self.assertEqual(
            [Rental(**x) for x in responses["Items"]],
            [Rental(id="W0820001", **rental.model_dump(mode="json"))],
        )
        self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], DeviceStatus.AVAILABLE)
        self.assertEqual(self.service.devices_table.scan()["Items"][1]["status"], DeviceStatus.RENTED)

        with self.assertRaises(
                NewDeviceNotFoundException,
                msg="Exception should be raised if rental specifies an unavailable device",
        ):
            self.service.insert_rental(rental=rental)
        self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], DeviceStatus.AVAILABLE)
        self.assertEqual(self.service.devices_table.scan()["Items"][1]["status"], DeviceStatus.RENTED)

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
        responses = self.service.rentals_table.scan()
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
