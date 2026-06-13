from moto import mock_aws

from api.src.exceptions import DeviceNotFoundException
from common.constants import DeviceType, Location, DeviceStatus
from common.data_models import NewDevice
from tests.unit.base_tests import BaseTestCases


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

        # New test: location not specified
        available_device_ids = self.service.get_available_device_ids(2025, DeviceType.SCOOTER)
        self.assertEqual(sorted(available_device_ids), ["S01", "S03"])

        available_device_ids = self.service.get_available_device_ids(2025, DeviceType.WHEELCHAIR)
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

    def test_get_device_by_id(self):
        self.assertIsNone(self.service.get_device_by_id(cne_year=2025, device_id="S01"))

        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.RENTED),
        ])

        device = self.service.get_device_by_id(cne_year=2025, device_id="W01")
        self.assertEqual(device["id"], "W01")
        self.assertEqual(device["status"], DeviceStatus.RENTED)
        self.assertEqual(device["location"], Location.PG)

        self.assertIsNone(self.service.get_device_by_id(cne_year=2025, device_id="W99"))
        self.assertIsNone(self.service.get_device_by_id(cne_year=2026, device_id="W01"))

    def test_get_devices_by_status(self):
        self.service.add_devices(devices=[
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC,
                      status=DeviceStatus.OUT_OF_SERVICE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG,
                      status=DeviceStatus.OUT_OF_SERVICE),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.BACKUP),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.PG, status=DeviceStatus.AVAILABLE),
        ])

        out_of_service = self.service.get_devices_by_status(cne_year=2025, status=DeviceStatus.OUT_OF_SERVICE)
        self.assertEqual(sorted(d["id"] for d in out_of_service), ["S01", "W01"])

        # filter by device type
        out_of_service_wc = self.service.get_devices_by_status(
            cne_year=2025, status=DeviceStatus.OUT_OF_SERVICE, device_type=DeviceType.WHEELCHAIR
        )
        self.assertEqual([d["id"] for d in out_of_service_wc], ["W01"])

        # filter by location
        out_of_service_pg = self.service.get_devices_by_status(
            cne_year=2025, status=DeviceStatus.OUT_OF_SERVICE, location=Location.PG
        )
        self.assertEqual([d["id"] for d in out_of_service_pg], ["W01"])

        backups = self.service.get_devices_by_status(cne_year=2025, status=DeviceStatus.BACKUP)
        self.assertEqual([d["id"] for d in backups], ["W02"])

        self.assertEqual(self.service.get_devices_by_status(cne_year=2025, status=DeviceStatus.RENTED), [])

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

    def test_count_available_devices_by_location(self):
        devices = [
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.PG, status=DeviceStatus.AVAILABLE),
            NewDevice(cne_year=2025, type=DeviceType.SCOOTER, location=Location.BLC, status=DeviceStatus.RENTED),
            NewDevice(cne_year=2025, type=DeviceType.WHEELCHAIR, location=Location.BLC, status=DeviceStatus.AVAILABLE),
        ]
        self.service.add_devices(devices)

        result = self.service.count_available_devices_by_location(cne_year=2025, device_type=DeviceType.SCOOTER)
        self.assertEqual({Location.BLC.value: 2, Location.PG.value: 1}, result)

        result = self.service.count_available_devices_by_location(cne_year=2025, device_type=DeviceType.WHEELCHAIR)
        self.assertEqual({Location.BLC.value: 1, Location.PG.value: 0}, result)
