from datetime import date

from moto import mock_aws

from api.src.exceptions import (
    DeviceNotFoundOrInvalidStatusException,
    NewReservationNotFoundOrNotEditableException,
)
from common.constants import DeviceStatus, DeviceType, Location, RentalStatus, ReservationStatus
from common.data_models import Rental, NewDevice, ChangeDeviceInfo
from tests.unit.base_tests import BaseTestCases


# pylint: disable=missing-class-docstring,missing-function-docstring
@mock_aws
class TestDynamoDBServiceRentals(BaseTestCases.BaseDynamoDBServiceTest):

    # pylint: disable=protected-access
    def test_get_new_rental_or_reservation_id(self):
        """Test the _get_new_rental_or_reservation_id method generates correct sequential IDs."""
        test_date = date(2025, 6, 21)

        # Test with empty table - should return ID with sequence 001
        rental_id = self.service._get_new_rental_or_reservation_id(
            table=self.service.rentals_table,
            cne_year=2025,
            date=test_date,
            device_type=DeviceType.WHEELCHAIR,
        )
        self.assertEqual(rental_id, "W0621001")

        # Add a few items with the same pattern and verify sequence increments
        self.service.rentals_table.put_item(
            Item={
                "cne_year": 2025,
                "id": "W0621001",
                "date": test_date.isoformat(),
                "device_type": DeviceType.WHEELCHAIR,
            }
        )

        # Get next ID - should be sequence 002
        rental_id = self.service._get_new_rental_or_reservation_id(
            table=self.service.rentals_table,
            cne_year=2025,
            date=test_date,
            device_type=DeviceType.WHEELCHAIR,
        )
        self.assertEqual(rental_id, "W0621002")

        # Add another item and check again
        self.service.rentals_table.put_item(
            Item={
                "cne_year": 2025,
                "id": "W0621002",
                "date": test_date.isoformat(),
                "device_type": DeviceType.WHEELCHAIR,
            }
        )

        # Get next ID - should be sequence 003
        rental_id = self.service._get_new_rental_or_reservation_id(
            table=self.service.rentals_table,
            cne_year=2025,
            date=test_date,
            device_type=DeviceType.WHEELCHAIR,
        )
        self.assertEqual(rental_id, "W0621003")

        # Test with a different device type
        rental_id = self.service._get_new_rental_or_reservation_id(
            table=self.service.rentals_table,
            cne_year=2025,
            date=test_date,
            device_type=DeviceType.SCOOTER,
        )
        self.assertEqual(rental_id, "S0621001")  # First scooter rental

        # Test with a different year - should start from 001
        rental_id = self.service._get_new_rental_or_reservation_id(
            table=self.service.rentals_table,
            cne_year=2026,
            date=test_date,
            device_type=DeviceType.WHEELCHAIR,
        )
        self.assertEqual(rental_id, "W0621001")  # First wheelchair rental for 2026

        # Test with a different date
        different_date = date(2025, 7, 15)
        rental_id = self.service._get_new_rental_or_reservation_id(
            table=self.service.rentals_table,
            cne_year=2025,
            date=different_date,
            device_type=DeviceType.WHEELCHAIR,
        )
        self.assertEqual(rental_id, "W0715001")  # First wheelchair rental for July 15

        # Verify items with similar but different prefixes don't affect sequence
        # Add a scooter rental with same date
        self.service.rentals_table.put_item(
            Item={
                "cne_year": 2025,
                "id": "S0621001",
                "date": test_date.isoformat(),
                "device_type": DeviceType.SCOOTER,
            }
        )

        # Check wheelchair sequence - still 003 (not affected by scooter)
        rental_id = self.service._get_new_rental_or_reservation_id(
            table=self.service.rentals_table,
            cne_year=2025,
            date=test_date,
            device_type=DeviceType.WHEELCHAIR,
        )
        self.assertEqual(rental_id, "W0621003")

        # Check scooter sequence - should be 002
        rental_id = self.service._get_new_rental_or_reservation_id(
            table=self.service.rentals_table,
            cne_year=2025,
            date=test_date,
            device_type=DeviceType.SCOOTER,
        )
        self.assertEqual(rental_id, "S0621002")

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

    def test_change_rental_device(self):
        self._setup_in_progress_rental()
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.BACKUP),
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
        ])

        # try changing to a device that should raise an error
        for new_device_id, subtest_msg in (
                ("W05", "Non-Existent Device"),
                ("S01", "Device of the wrong type"),
                ("W03", "Device of the wrong status"),
        ):
            with self.subTest(msg=subtest_msg):
                with self.assertRaises(DeviceNotFoundOrInvalidStatusException):
                    self.service.change_rental_device(
                        change_info=ChangeDeviceInfo(
                            cne_year=2025,
                            date=date(2025, 8, 20),
                            id="W0820001",
                            device_type=DeviceType.WHEELCHAIR,
                            location=Location.BLC,
                            old_device_id="W01",
                            new_device_id=new_device_id,
                            staff_name="Test Staff",
                        )

                    )
                self.assertEqual(self.service.rentals_table.scan()["Items"][0]["device_id"], "W01")
                for device in self.service.devices_table.scan()["Items"]:
                    self.assertEqual(device["status"] == DeviceStatus.RENTED, device["id"] == "W01")

        # try a proper change that should work
        self.service.change_rental_device(
            change_info=ChangeDeviceInfo(
                cne_year=2025,
                date=date(2025, 8, 20),
                id="W0820001",
                device_type=DeviceType.WHEELCHAIR,
                location=Location.BLC,
                old_device_id="W01",
                new_device_id="W02",
                staff_name="Test Staff",
            )
        )
        self.assertEqual(self.service.rentals_table.scan()["Items"][0]["device_id"], "W02")
        for device in self.service.devices_table.scan()["Items"]:
            self.assertEqual(device["status"] == DeviceStatus.RENTED, device["id"] == "W02")

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
                        DeviceNotFoundOrInvalidStatusException,
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
                DeviceNotFoundOrInvalidStatusException,
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
                DeviceNotFoundOrInvalidStatusException,
                msg="Exception should be raised if rental specifies a non-existent device",
        ):
            self.service.insert_rental(rental=rental)

        # inserting a device of the wrong type, error should still be raised
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        with self.assertRaises(
                DeviceNotFoundOrInvalidStatusException,
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
                DeviceNotFoundOrInvalidStatusException,
                msg="Exception should be raised if rental specifies an unavailable device",
        ):
            self.service.insert_rental(rental=rental)
        self.assertEqual(self.service.devices_table.scan()["Items"][0]["status"], DeviceStatus.AVAILABLE)
        self.assertEqual(self.service.devices_table.scan()["Items"][1]["status"], DeviceStatus.RENTED)

    def test_get_rental_by_id(self):
        self.assertIsNone(self.service.get_rental_by_id(cne_year=2025, rental_id="W0820001"))

        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        rental = self._generate_mock_new_rental(overrides={"reservation_id": None})
        rental_id = self.service.insert_rental(rental=rental)

        item = self.service.get_rental_by_id(cne_year=2025, rental_id=rental_id)
        self.assertIsNotNone(item)
        self.assertEqual(Rental(**item), Rental(id=rental_id, **rental.model_dump(mode="json")))

        self.assertIsNone(self.service.get_rental_by_id(cne_year=2025, rental_id="W0820099"))
        self.assertIsNone(self.service.get_rental_by_id(cne_year=2026, rental_id=rental_id))

    def test_get_current_rental_for_device(self):
        self.assertIsNone(self.service.get_current_rental_for_device(cne_year=2025, device_id="W01"))

        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE)
        ])
        rental = self._generate_mock_new_rental(overrides={"reservation_id": None})
        rental_id = self.service.insert_rental(rental=rental)

        item = self.service.get_current_rental_for_device(cne_year=2025, device_id="W01")
        self.assertEqual(item["id"], rental_id)
        self.assertEqual(item["status"], RentalStatus.IN_PROGRESS)

        # a device with no in-progress rental returns None
        self.assertIsNone(self.service.get_current_rental_for_device(cne_year=2025, device_id="W02"))

        # once completed, the device no longer has a current rental
        completed_rental = self._generate_mock_completed_rental(overrides={"id": rental_id, "reservation_id": None})
        self.service.complete_rental(rental=completed_rental)
        self.assertIsNone(self.service.get_current_rental_for_device(cne_year=2025, device_id="W01"))

    def test_get_outstanding_rentals(self):
        self.assertEqual(self.service.get_outstanding_rentals(cne_year=2025), [])

        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
        ])
        wheelchair_rental = self._generate_mock_new_rental(overrides={"reservation_id": None})
        self.service.insert_rental(rental=wheelchair_rental)
        scooter_rental = self._generate_mock_new_rental(overrides={
            "reservation_id": None, "device_id": "S01", "device_type": DeviceType.SCOOTER,
        })
        scooter_rental_id = self.service.insert_rental(rental=scooter_rental)

        outstanding = self.service.get_outstanding_rentals(cne_year=2025)
        self.assertEqual(len(outstanding), 2)

        # filter by device type
        outstanding_wc = self.service.get_outstanding_rentals(cne_year=2025, device_type=DeviceType.WHEELCHAIR)
        self.assertEqual([r["device_id"] for r in outstanding_wc], ["W01"])

        # completing a rental drops it from the outstanding list
        completed_rental = self._generate_mock_completed_rental(overrides={
            "id": scooter_rental_id, "device_id": "S01", "reservation_id": None,
        })
        self.service.complete_rental(rental=completed_rental)
        outstanding = self.service.get_outstanding_rentals(cne_year=2025)
        self.assertEqual([r["device_id"] for r in outstanding], ["W01"])

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

    def test_count_rentals_on_date(self):
        for rental_id, status in [
            ("W0820001", RentalStatus.IN_PROGRESS),
            ("W0820002", RentalStatus.COMPLETED),
            ("S0820001", RentalStatus.IN_PROGRESS),
        ]:
            self.service.rentals_table.put_item(Item={
                "cne_year": 2025, "id": rental_id, "date": "2025-08-20", "status": status,
                "device_type": DeviceType.WHEELCHAIR if rental_id.startswith("W") else DeviceType.SCOOTER,
            })

        self.assertEqual(3, self.service.count_rentals_on_date(date=date(2025, 8, 20)))
        self.assertEqual(2,
                         self.service.count_rentals_on_date(date=date(2025, 8, 20), device_type=DeviceType.WHEELCHAIR))
        self.assertEqual(1, self.service.count_rentals_on_date(date=date(2025, 8, 20), device_type=DeviceType.SCOOTER))
        self.assertEqual(2, self.service.count_rentals_on_date(date=date(2025, 8, 20), in_progress_rentals_only=True))
        self.assertEqual(0, self.service.count_rentals_on_date(date=date(2025, 8, 21)))
