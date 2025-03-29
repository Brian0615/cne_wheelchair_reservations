from functools import wraps
from typing import List

import boto3
import botocore

from api.src.exceptions import DeviceNotFoundException
from common.constants import DeviceType, Location, DeviceStatus
from common.data_models import NewDevice
from common.logger import initialize_logger, timeit


logger = initialize_logger()


class DynamoDBService:
    """Service class to interact with DynamoDB."""

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.devices_table = self.dynamodb.Table('cne_devices')
        self.rentals_table = self.dynamodb.Table('cne_rentals')
        self.reservations_table = self.dynamodb.Table('cne_reservations')

    # ==============================
    # HELPER FUNCTIONS
    # ==============================

    @staticmethod
    def _auto_raise_device_not_found_exception(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except botocore.exceptions.ClientError as exc:
                if exc.response["Error"]["Code"] == "TransactionCanceledException":
                    if "ConditionalCheckFailed" in exc.response["CancellationReasons"][0]["Code"]:
                        # This means that the device was not found in the inventory
                        logger.warning("One or more devices not found in the inventory. No devices were deleted.")
                        raise DeviceNotFoundException(
                            f"At least one of the following devices were not found in the inventory: "
                            f"{kwargs.get('device_ids', [])} (year={kwargs.get('cne_year', '')})",
                        ) from exc
                raise exc

        return wrapper

    # ==============================
    # DEVICES
    # ==============================

    @timeit(logger=logger)
    def add_devices(self, devices: List[NewDevice]):
        """Add devices to the inventory"""
        response = self.devices_table.scan(ProjectionExpression="cne_year, id")

        # identify the next available IDs for each device type and year in the database
        existing_ids = {
            prefix: {
                year: [
                    int(item["id"][1:])
                    for item in response["Items"]
                    if item["id"].startswith(prefix) and item["cne_year"] == year
                ] for year in set(item["cne_year"] for item in response["Items"])
            }
            for prefix in [x.get_prefix() for x in DeviceType]
        }
        next_ids = {
            prefix: {year: max(existing_ids[prefix].get(year, [0]), default=0) + 1 for year in existing_ids[prefix]}
            for prefix in [x.get_prefix() for x in DeviceType]
        }

        for device in devices:
            prefix = device.type.value[0].upper()
            year = device.cne_year
            try:
                device.id = f"{prefix}{next_ids[prefix][year]:02}"
            except KeyError:  # a year that does not yet exist in the database
                next_ids[prefix][year] = 1
                device.id = f"{prefix}{next_ids[prefix][year]:02}"
            self.devices_table.put_item(Item=device.model_dump())
            next_ids[prefix][year] += 1

        logger.info("Added devices to the inventory: %s", devices)

    @timeit(logger=logger)
    def get_available_device_ids(self, cne_year: int, device_type: DeviceType, location: Location):
        """Get the available devices of a specific type at a specific location"""
        response = self.devices_table.scan(
            FilterExpression="cne_year = :year AND #type = :type AND #location = :location AND #status = :status",
            ExpressionAttributeNames={
                "#type": "type",
                "#location": "location",
                "#status": "status"
            },
            ExpressionAttributeValues={
                ":year": cne_year,
                ":type": device_type,
                ":location": location,
                ":status": DeviceStatus.AVAILABLE
            }
        )
        return [item["id"] for item in response["Items"]]

    @timeit(logger=logger)
    def get_full_inventory(self, cne_year: int):
        """Get the full inventory of devices"""
        response = self.devices_table.scan(
            FilterExpression="cne_year = :year",
            ExpressionAttributeValues={":year": cne_year}
        )
        return response["Items"]

    @timeit(logger=logger)
    @_auto_raise_device_not_found_exception
    def remove_devices(self, cne_year: int, device_ids: List[str]):
        """Remove devices from the inventory"""
        self.dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    "Delete": {
                        "TableName": self.devices_table.name,
                        "Key": {"cne_year": cne_year, "id": device_id},
                        "ConditionExpression": "attribute_exists(cne_year) AND attribute_exists(id)",
                    }
                }
                for device_id in device_ids
            ]
        )

    @timeit(logger=logger)
    @_auto_raise_device_not_found_exception
    def update_devices_location(self, cne_year: int, device_ids: List[str], location: str):
        """Update the location of devices"""
        self.dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": self.devices_table.name,
                        "Key": {"cne_year": cne_year, "id": device_id},
                        "UpdateExpression": "SET #location = :location",
                        "ExpressionAttributeNames": {"#location": "location"},
                        "ExpressionAttributeValues": {":location": location},
                        "ConditionExpression": "attribute_exists(cne_year) AND attribute_exists(id)",
                    }
                }
                for device_id in device_ids
            ]
        )

    @timeit(logger=logger)
    @_auto_raise_device_not_found_exception
    def update_devices_status(self, cne_year: int, device_ids: List[str], status: DeviceStatus):
        """Update the status of devices"""
        self.dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": self.devices_table.name,
                        "Key": {"cne_year": cne_year, "id": device_id},
                        "UpdateExpression": "SET #status = :status",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": {":status": status},
                        "ConditionExpression": "attribute_exists(cne_year) AND attribute_exists(id)",
                    }
                }
                for device_id in device_ids
            ]
        )
