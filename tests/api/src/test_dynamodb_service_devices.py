from moto import mock_aws

from api.src.exceptions import DeviceNotFoundException
from common.constants import DeviceType, Location, DeviceStatus
from common.data_models import NewDevice
from tests.base_tests import BaseTestCases


# pylint: disable=missing-class-docstring,missing-function-docstring
@mock_aws
class TestDynamoDBServiceDevices(BaseTestCases.BaseDynamoDBServiceTest):

    def test_add_devices(self):
        devices = [
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2026, type=DeviceType.SCOOTER, location=Location.PG, status=DeviceStatus.AVAILABLE)
        ]
        self.service.add_devices(devices)

        response = self.service.devices_table.scan()
        items = response["Items"]
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0]["cne_year"], 2025)
        self.assertEqual(items[0]["id"], "S01")
        self.assertEqual(items[1]["cne_year"], 2025)
        self.assertEqual(items[1]["id"], "W01")
        self.assertEqual(items[2]["cne_year"], 2025)
        self.assertEqual(items[2]["id"], "W02")
        self.assertEqual(items[3]["cne_year"], 2026)
        self.assertEqual(items[3]["id"], "S01")

        devices = [
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2026, type=DeviceType.SCOOTER, location=Location.PG, status=DeviceStatus.AVAILABLE)
        ]
        self.service.add_devices(devices)

    def test_get_available_device_ids(self):
        devices = [
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.BACKUP),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.RENTED),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.PG, status=DeviceStatus.AVAILABLE)
        ]
        self.service.add_devices(devices)

        available_device_ids = self.service.get_available_device_ids(2025, DeviceType.SCOOTER, Location.BLC)
        self.assertEqual(sorted(available_device_ids), ["S01"])

        available_device_ids = self.service.get_available_device_ids(2025, DeviceType.SCOOTER, Location.PG)
        self.assertEqual(sorted(available_device_ids), ["S03"])

        available_device_ids = self.service.get_available_device_ids(2025, DeviceType.WHEELCHAIR, Location.BLC)
        self.assertEqual(sorted(available_device_ids), [])

        available_device_ids = self.service.get_available_device_ids(2025, DeviceType.WHEELCHAIR, Location.PG)
        self.assertEqual(sorted(available_device_ids), ["W02", "W03"])

    def test_get_full_inventory(self):
        devices = [
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE)
        ]
        self.service.add_devices(devices)

        response = self.service.get_full_inventory(cne_year=2025)
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["cne_year"], 2025)
        self.assertEqual(response[0]["id"], "S01")
        self.assertEqual(response[1]["cne_year"], 2025)
        self.assertEqual(response[1]["id"], "W01")

        response = self.service.get_full_inventory(cne_year=2026)
        self.assertEqual(len(response), 0)

    def test_remove_devices(self):
        devices = [
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE)
        ]
        self.service.add_devices(devices)

        self.service.remove_devices(2025, ["S01"])
        response = self.service.devices_table.scan()
        items = response["Items"]
        self.assertEqual(len(items), 1)

        self.service.remove_devices(2025, ["W01"])
        response = self.service.devices_table.scan()
        items = response["Items"]
        self.assertEqual(len(items), 0)

        with self.assertRaises(DeviceNotFoundException, msg="Deleting a non-existing device should raise an error"):
            self.service.remove_devices(2025, ["S01"])

    def test_update_devices_location(self):
        devices = [
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE)
        ]
        self.service.add_devices(devices)

        self.service.update_devices_location(2025, ["S01"], Location.PG)
        response = self.service.devices_table.scan()
        items = response["Items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["location"], Location.PG)
        self.assertEqual(items[1]["location"], Location.PG)

        with self.assertRaises(DeviceNotFoundException, msg="Updating a non-existing device should raise an error"):
            self.service.update_devices_location(2025, ["S05"], Location.BLC)

    def test_update_devices_status(self):
        devices = [
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE)
        ]
        self.service.add_devices(devices)

        self.service.update_devices_status(2025, ["S01"], DeviceStatus.RENTED)
        response = self.service.devices_table.scan()
        items = response["Items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["status"], DeviceStatus.RENTED)
        self.assertEqual(items[1]["status"], DeviceStatus.AVAILABLE)

        with self.assertRaises(DeviceNotFoundException, msg="Updating a non-existing device should raise an error"):
            self.service.update_devices_status(2025, ["S05"], DeviceStatus.BACKUP)
