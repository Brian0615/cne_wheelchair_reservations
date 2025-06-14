import os
from datetime import datetime
from functools import wraps
from typing import List, Optional

import boto3
import botocore
from boto3.dynamodb.conditions import Attr, Key

from api.src.exceptions import (
    DeviceNotFoundException,
    NewDeviceNotFoundException,
    NewReservationNotFoundOrNotEditableException,
    ReservationNotFoundOrNotEditableException,
    RentalNotFoundOrNotEditableException
)
from common.constants import DeviceType, Location, DeviceStatus, ReservationStatus, RentalStatus
from common.data_models import CompletedRental, NewDevice, NewReservation, Reservation, NewRental, ChangeDeviceInfo
from common.logger import initialize_logger, timeit
from common.utils import read_secret

logger = initialize_logger()


class DynamoDBService:
    """Service class to interact with DynamoDB."""

    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=read_secret(os.getenv("AWS_ACCESS_KEY_ID")),
            aws_secret_access_key=read_secret(os.getenv("AWS_SECRET_ACCESS_KEY")),
        )
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

    @staticmethod
    def _auto_raise_reservation_not_found_exception(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except botocore.exceptions.ClientError as exc:
                if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    logger.warning("One or more devices not found in the inventory. No devices were deleted.")
                    reservation_id = None
                    if "reservation" in kwargs:
                        reservation_id = kwargs.get("reservation").id
                    if "reservation_id" in kwargs:
                        reservation_id = kwargs.get("reservation_id")
                    raise ReservationNotFoundOrNotEditableException(
                        f"The reservation was either not found or cannot be updated due to its current status "
                        f"(year={kwargs.get('cne_year', '')})"
                        + (f": {reservation_id}" if reservation_id else "")
                    ) from exc
                raise exc

        return wrapper

    @staticmethod
    def _get_new_rental_or_reservation_id(table, cne_year: int, date: datetime.date, device_type: DeviceType):
        response = table.query(
            KeyConditionExpression=Key("cne_year").eq(cne_year),
            FilterExpression=Attr("date").eq(date.isoformat()) & Attr('device_type').eq(device_type),
        )
        count = len(response['Items'])

        return f"{device_type.get_prefix()}{date.strftime('%m%d')}{str(count + 1).zfill(3)}"

    # pylint: disable=too-many-arguments
    def _form_update_device_transact_dict(
            self,
            cne_year: int,
            device_id: str,
            update_location: Location,
            update_status: DeviceStatus,
            expected_status: Optional[DeviceStatus] = None,
            expected_type: Optional[DeviceType] = None,
    ) -> dict:
        """
        Form a transaction dictionary to update a device's location and status in DynamoDB,
        optionally checking for an expected current status and type for the device
        """

        condition_expression = "attribute_exists(cne_year) AND attribute_exists(id)"
        expression_attribute_names = {"#status": "status", "#location": "location"}
        expression_attribute_values = {":update_status": update_status, ":update_location": update_location}
        if expected_status:
            condition_expression += " AND #status = :expected_status"
            expression_attribute_values[":expected_status"] = expected_status
        if expected_type:
            condition_expression += " AND #type = :expected_type"
            expression_attribute_names["#type"] = "type"
            expression_attribute_values[":expected_type"] = expected_type

        return {
            "Update": {
                "TableName": self.devices_table.name,
                "Key": {"cne_year": cne_year, "id": device_id},
                "ConditionExpression": condition_expression,
                "UpdateExpression": "SET #status = :update_status, #location = :update_location",
                "ExpressionAttributeNames": expression_attribute_names,
                "ExpressionAttributeValues": expression_attribute_values,
            }
        }

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


    # ==============================
    # RENTALS
    # ==============================

    @timeit(logger=logger)
    def change_rental_device(self, change_info: ChangeDeviceInfo):
        """Change the device of a rental."""
        transact_items = [
            self._form_update_device_transact_dict(
                cne_year=change_info.cne_year,
                device_id=change_info.old_device_id,
                update_location=change_info.location,
                update_status=DeviceStatus.AVAILABLE,
                expected_status=DeviceStatus.RENTED,
            ),
            self._form_update_device_transact_dict(
                cne_year=change_info.cne_year,
                device_id=change_info.new_device_id,
                update_location=change_info.location,
                update_status=DeviceStatus.RENTED,
                expected_status=DeviceStatus.AVAILABLE,
                expected_type=change_info.device_type,
            ),
            {  # update rental
                "Update": {
                    "TableName": self.rentals_table.name,
                    "Key": {"cne_year": change_info.cne_year, "id": change_info.id},
                    "ConditionExpression": (
                        "attribute_exists(cne_year) AND attribute_exists(id) AND #status = :in_progress_status"
                    ),
                    "UpdateExpression": "SET #device_id = :device_id",
                    "ExpressionAttributeNames": {
                        "#device_id": "device_id",
                        "#status": "status",
                    },
                    "ExpressionAttributeValues": {
                        ":device_id": change_info.new_device_id,
                        ":in_progress_status": RentalStatus.IN_PROGRESS,
                    },
                }
            }
        ]

        try:
            self.dynamodb.meta.client.transact_write_items(TransactItems=transact_items)
        except botocore.exceptions.ClientError as exc:
            if exc.response["Error"]["Code"] == "TransactionCanceledException":
                cancellation_reasons = exc.response["CancellationReasons"]
                if cancellation_reasons[0]["Code"] == "ConditionalCheckFailed":
                    raise NewDeviceNotFoundException(
                        cne_year=change_info.cne_year,
                        device_id=change_info.old_device_id
                    ) from exc
                if cancellation_reasons[1]["Code"] == "ConditionalCheckFailed":
                    raise NewDeviceNotFoundException(
                        cne_year=change_info.cne_year,
                        device_id=change_info.new_device_id
                    ) from exc
                if cancellation_reasons[2]["Code"] == "ConditionalCheckFailed":
                    raise RentalNotFoundOrNotEditableException(
                        cne_year=change_info.cne_year,
                        rental_id=change_info.id,
                    ) from exc
            raise exc

    @timeit(logger=logger)
    def complete_rental(self, rental: CompletedRental):
        """Complete a rental."""
        transact_items = [
            self._form_update_device_transact_dict(
                cne_year=rental.cne_year,
                device_id=rental.device_id,
                update_location=rental.return_location,
                update_status=DeviceStatus.AVAILABLE,
                expected_status=DeviceStatus.RENTED,
            ),
            {
                "Update": {
                    "TableName": self.rentals_table.name,
                    "Key": {"cne_year": rental.cne_year, "id": rental.id},
                    "ConditionExpression": (
                        "attribute_exists(cne_year) AND attribute_exists(id) "
                        "AND NOT (#status in (:completed_status))"
                    ),
                    "UpdateExpression": (
                        "SET #status = :status, "
                        "#return_location = :return_location, "
                        "#return_time = :return_time, "
                        "#return_staff_name = :return_staff_name "
                    ),
                    "ExpressionAttributeNames": {
                        "#status": "status",
                        "#return_location": "return_location",
                        "#return_time": "return_time",
                        "#return_staff_name": "return_staff_name",
                    },
                    "ExpressionAttributeValues": {
                        ":completed_status": RentalStatus.COMPLETED,
                        ":status": RentalStatus.COMPLETED,
                        ":return_location": rental.return_location,
                        ":return_time": rental.return_time.isoformat(),
                        ":return_staff_name": rental.return_staff_name,
                    },
                }
            }
        ]
        if rental.reservation_id:
            transact_items.append(
                {
                    "Update": {
                        "TableName": self.reservations_table.name,
                        "Key": {"cne_year": rental.cne_year, "id": rental.reservation_id},
                        "ConditionExpression": (
                            "attribute_exists(cne_year) AND attribute_exists(id) "
                            "AND #status = :picked_up_status"
                        ),
                        "UpdateExpression": "SET #status = :status",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": {
                            ":picked_up_status": ReservationStatus.PICKED_UP,
                            ":status": ReservationStatus.COMPLETED,
                        },
                    }
                }
            )

        try:
            self.dynamodb.meta.client.transact_write_items(TransactItems=transact_items)
        except botocore.exceptions.ClientError as exc:
            if exc.response["Error"]["Code"] == "TransactionCanceledException":
                cancellation_reasons = exc.response["CancellationReasons"]
                if cancellation_reasons[0]["Code"] == "ConditionalCheckFailed":
                    raise NewDeviceNotFoundException(cne_year=rental.cne_year, device_id=rental.device_id) from exc
                if cancellation_reasons[1]["Code"] == "ConditionalCheckFailed":
                    raise RentalNotFoundOrNotEditableException(cne_year=rental.cne_year, rental_id=rental.id) from exc
                if rental.reservation_id and cancellation_reasons[2]["Code"] == "ConditionalCheckFailed":
                    raise NewReservationNotFoundOrNotEditableException(
                        cne_year=rental.cne_year,
                        reservation_id=rental.reservation_id,
                    ) from exc
            raise exc
        logger.info("Completed rental: %s", rental.id)

    def get_rentals_on_date(
            self,
            date: datetime.date,
            device_type: DeviceType = None,
            in_progress_rentals_only: bool = False,
    ):
        """Get all rentals on a given date"""
        key_condition_expression = Key("cne_year").eq(date.year)
        filter_expression = Attr("date").eq(date.isoformat())

        if device_type:
            filter_expression &= Attr("device_type").eq(device_type)

        if in_progress_rentals_only:
            filter_expression &= Attr("status").eq(RentalStatus.IN_PROGRESS)

        response = self.rentals_table.query(
            KeyConditionExpression=key_condition_expression,
            FilterExpression=filter_expression,
            ProjectionExpression=(
                "cne_year, id, #date, device_id, device_type, pickup_location, pickup_time, reservation_id, #name, "
                "phone_number, deposit_payment_method, items_left_behind, notes, return_location, return_time"
            ),
            ExpressionAttributeNames={"#date": "date", "#name": "name"},
        )

        return response.get("Items", [])

    @timeit(logger=logger)
    def insert_rental(self, rental: NewRental):
        """Insert a new rental."""
        rental_id = self._get_new_rental_or_reservation_id(
            table=self.rentals_table,
            cne_year=rental.cne_year,
            date=rental.date,
            device_type=rental.device_type,
        )

        transact_items = [
            self._form_update_device_transact_dict(
                cne_year=rental.cne_year,
                device_id=rental.device_id,
                update_location=rental.pickup_location,
                update_status=DeviceStatus.RENTED,
                expected_status=DeviceStatus.AVAILABLE,
                expected_type=rental.device_type,
            ),
            {
                "Put": {
                    "TableName": self.rentals_table.name,
                    "Item": {"id": rental_id, **rental.model_dump(mode="json")},
                }
            },
        ]
        if rental.reservation_id:
            transact_items.append(
                {
                    "Update": {
                        "TableName": self.reservations_table.name,
                        "Key": {"cne_year": rental.cne_year, "id": rental.reservation_id},
                        "ConditionExpression": (
                            "attribute_exists(cne_year) "
                            "AND attribute_exists(id) "
                            "AND NOT (#status in (:cancelled, :completed, :picked_up))"
                        ),
                        "UpdateExpression": "SET #status = :status, #rental_id = :rental_id",
                        "ExpressionAttributeNames": {
                            "#status": "status",
                            "#rental_id": "rental_id",
                        },
                        "ExpressionAttributeValues": {
                            ":cancelled": ReservationStatus.CANCELLED,
                            ":completed": ReservationStatus.COMPLETED,
                            ":picked_up": ReservationStatus.PICKED_UP,
                            ":status": ReservationStatus.PICKED_UP,
                            ":rental_id": rental_id,
                        },
                    }
                }
            )

        try:
            self.dynamodb.meta.client.transact_write_items(TransactItems=transact_items)
        except botocore.exceptions.ClientError as exc:
            if exc.response["Error"]["Code"] == "TransactionCanceledException":
                cancellation_reasons = exc.response["CancellationReasons"]
                if cancellation_reasons[0]["Code"] == "ConditionalCheckFailed":
                    raise NewDeviceNotFoundException(cne_year=rental.cne_year, device_id=rental.device_id) from exc
                if rental.reservation_id and cancellation_reasons[2]["Code"] == "ConditionalCheckFailed":
                    raise NewReservationNotFoundOrNotEditableException(
                        cne_year=rental.cne_year,
                        reservation_id=rental.reservation_id,
                    ) from exc
            raise exc
        logger.info("Inserted new rental: %s", rental_id)
        return rental_id


    # ==============================
    # RESERVATIONS
    # ==============================

    @timeit(logger=logger)
    def get_reservations_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
            exclude_picked_up_reservations: bool = False,
    ) -> List[dict]:
        """Get all reservations on a given date."""
        key_condition_expression = Key('cne_year').eq(date.year)
        filter_expression = Attr('date').eq(date.isoformat())

        if device_type:
            filter_expression = Attr('device_type').eq(device_type)

        if exclude_picked_up_reservations:
            filter_expression &= ~Attr('status').is_in([
                ReservationStatus.PICKED_UP,
                ReservationStatus.COMPLETED,
                ReservationStatus.CANCELLED,
            ])

        response = self.reservations_table.query(
            KeyConditionExpression=key_condition_expression,
            FilterExpression=filter_expression
        )

        return response.get('Items', [])

    @timeit(logger=logger)
    def insert_reservation(self, reservation: NewReservation):
        """Insert a new reservation."""
        reservation.id = self._get_new_rental_or_reservation_id(
            table=self.reservations_table,
            cne_year=reservation.cne_year,
            date=reservation.date,
            device_type=reservation.device_type,
        )
        self.reservations_table.put_item(Item=reservation.model_dump(mode="json"))
        logger.info("Inserted new reservation: %s", reservation.id)

        return reservation.id

    def _update_reservation_helper(
            self,
            key: dict,
            update_expression: str,
            expression_attribute_names: dict,
            expression_attribute_values: dict,
    ):
        self.reservations_table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression=(
                Attr("cne_year").exists()
                & Attr("id").exists()
                & ~Attr("status").is_in(
                    [
                        ReservationStatus.CANCELLED,
                        ReservationStatus.COMPLETED,
                        ReservationStatus.PICKED_UP
                    ]
                )
            ),
        )

    @timeit(logger=logger)
    @_auto_raise_reservation_not_found_exception
    def update_reservation(self, reservation: Reservation):
        """Update an existing reservation in the DynamoDB table."""
        key_dict = {"cne_year": reservation.cne_year, "id": reservation.id}

        # remove cne_year and id from update expression as it is part of key
        reservation = reservation.model_dump(mode="json")
        reservation.pop("cne_year")
        reservation.pop("id")
        self._update_reservation_helper(
            key=key_dict,
            update_expression="SET " + ", ".join(f"#{k} = :{k}" for k in reservation.keys()),
            expression_attribute_names={f"#{k}": k for k in reservation.keys()},
            expression_attribute_values={f":{k}": v for k, v in reservation.items()}
        )

    @timeit(logger=logger)
    @_auto_raise_reservation_not_found_exception
    def update_reservation_status(self, cne_year: int, reservation_id: str, status: ReservationStatus):
        """Update the status of an existing reservation in the DynamoDB table"""
        self._update_reservation_helper(
            key={"cne_year": cne_year, "id": reservation_id},
            update_expression="SET #status = :status",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={":status": status},
        )
