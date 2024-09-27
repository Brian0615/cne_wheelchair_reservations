# pylint: disable=not-context-manager

import datetime
import os
from typing import List, Optional

import pandas as pd
import psycopg
from psycopg import sql

from api.src.constants import Table
from api.src.exceptions import UniqueViolation
from common.constants import DeviceStatus, DeviceType, Location, ReservationStatus
from common.data_models.device import Device
from common.data_models.reservation import NewReservation


class DataService:
    """Service class to interact with the PostgreSQL database."""

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            host: str = os.environ["POSTGRES_HOST"],
            port: int = os.environ["POSTGRES_PORT"],
            username: str = os.environ["POSTGRES_USERNAME"],
            password: str = os.environ["POSTGRES_PASSWORD"],
            db_name: str = os.environ["POSTGRES_DB_NAME"],
            schema: str = os.environ["POSTGRES_SCHEMA"],
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_name = db_name
        self.schema = schema

    def __initialize_handle(self):
        return psycopg.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            dbname=self.db_name,
        )

    def __form_select_all_query(self, table_name: Table) -> sql.Composed:
        """Form a query to select all rows from a table in the database"""
        return (
            sql.SQL("SELECT * FROM {schema}.{table}")
            .format(schema=sql.Identifier(self.schema), table=sql.Identifier(table_name))
        )

    def get_full_inventory(self):
        """Get the full inventory of devices from the database."""
        with self.__initialize_handle() as handle:
            with handle.cursor() as cursor:
                cursor.execute(self.__form_select_all_query(table_name=Table.DEVICES))
                result = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
        return pd.DataFrame(result, columns=col_names)

    def select_available_device_ids(self, device_type: DeviceType, location: Location):
        """Get all available devices of a given type at a given location."""

        with open(
                os.path.join(os.path.dirname(__file__), "sql/get_available_device_ids.sql"),
                mode="r",
                encoding="utf-8",
        ) as file:
            select_query = sql.SQL(file.read()).format(
                schema=sql.Identifier(self.schema),
                table=sql.Identifier(Table.DEVICES),
                device_type=sql.Literal(device_type.value),
                status=sql.Literal(DeviceStatus.AVAILABLE.value),
                location=sql.Literal(location.value),
            )

        with self.__initialize_handle() as handle:
            with handle.cursor() as cursor:
                cursor.execute(select_query)
                result = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
        return pd.DataFrame(result, columns=col_names)["id"].tolist()

    def insert_devices(self, devices: List[Device]):
        """Add devices to the inventory in the database. Will raise an error if there are any conflicts."""

        self._insert_or_update_devices_helper(devices, insert_only=True)

    def update_devices(self, devices: List[Device]):
        """
        Update devices in the database.
        Will insert for any non-existing devices, and overwrite any existing devices
        """

        self._insert_or_update_devices_helper(devices, insert_only=False)

    def _insert_or_update_devices_helper(self, devices: List[Device], insert_only: bool):
        """
        Helper function to insert or update devices in the database.
        If insert_only is False, will insert for any non-existing devices, and overwrite any existing devices.
        """

        query_filename = "insert_devices.sql" if insert_only else "update_devices.sql"
        with open(
                os.path.join(os.path.dirname(__file__), f"sql/{query_filename}"),
                mode="r",
                encoding="utf-8",
        ) as file:
            query = sql.SQL(file.read()).format(
                schema=sql.Identifier(self.schema),
                table=sql.Identifier(Table.DEVICES),
                id=sql.Placeholder(),
                type=sql.Placeholder(),
                status=sql.Placeholder(),
                location=sql.Placeholder(),
            )

        with self.__initialize_handle() as handle:
            with handle.cursor() as cursor:
                try:
                    cursor.executemany(
                        query,
                        [(device.id, device.type, device.status, device.location) for device in devices],
                    )
                except psycopg.errors.UniqueViolation as exc:
                    handle.rollback()
                    raise UniqueViolation(exc.diag.message_primary + " - " + exc.diag.message_detail) from exc

    def insert_new_reservation(self, reservation: NewReservation) -> str:
        """Create a reservation in the database."""

        # load the query from file
        with open(
                os.path.join(os.path.dirname(__file__), "sql/insert_new_reservation.sql"),
                mode="r",
                encoding="utf-8",
        ) as file:
            insert_query = sql.SQL(file.read()).format(
                device_type_prefix=sql.Placeholder(),
                schema=sql.Identifier(self.schema),
                table=sql.Identifier(Table.RESERVATIONS),
                date=sql.Placeholder(),
                device_type=sql.Placeholder(),
                name=sql.Placeholder(),
                phone_number=sql.Placeholder(),
                location=sql.Placeholder(),
                pickup_time=sql.Placeholder(),
                status=sql.Placeholder(),
            )

        # execute the query and return the created reservation ID
        with self.__initialize_handle() as handle:
            with handle.cursor() as cursor:
                cursor.execute(
                    insert_query,
                    (
                        reservation.device_type.get_device_prefix(),
                        reservation.date,
                        reservation.date,
                        reservation.date,
                        reservation.device_type,
                        reservation.name,
                        reservation.phone_number,
                        reservation.location,
                        reservation.pickup_time,
                        ReservationStatus.get_default_reservation_status(device_type=reservation.device_type),
                    )
                )
                result = cursor.fetchall()
        return result[0][0]

    def get_reservations_on_date(self, date: datetime.date, device_type: Optional[DeviceType] = None) -> pd.DataFrame:
        """Get all reservations on a given date."""
        with open(
                os.path.join(os.path.dirname(__file__), "sql/get_reservations_on_date.sql"),
                mode="r",
                encoding="utf-8",
        ) as file:
            select_query = sql.SQL(file.read()).format(
                schema=sql.Identifier(self.schema),
                table=sql.Identifier(Table.RESERVATIONS),
                date=sql.Placeholder(),
                device_type=sql.Placeholder(),
            )

        with self.__initialize_handle() as handle:
            with handle.cursor() as cursor:
                cursor.execute(select_query, (date, device_type, device_type))
                result = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
        return pd.DataFrame(result, columns=col_names)
