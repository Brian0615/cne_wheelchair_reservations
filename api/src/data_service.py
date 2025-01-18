# pylint: disable=not-context-manager

import datetime
import os
from pathlib import Path
from typing import List, Optional, LiteralString

import pandas as pd
import psycopg
from psycopg import sql, Connection
from psycopg.types.enum import EnumInfo, register_enum

from common.constants import DeviceStatus, DeviceType, HoldItem, Location, PaymentMethod, ReservationStatus, Table
from common.data_models import ChangeDeviceInfo, CompletedRental, Device, NewRental, NewReservation


class DataService:
    """Service class to interact with the PostgreSQL database."""

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            host: str = os.environ["POSTGRES_HOST"],
            port: str = os.environ["POSTGRES_PORT"],
            username: str = os.environ["POSTGRES_USERNAME"],
            password: str = os.environ["POSTGRES_PASSWORD"],
            db_name: str = os.environ["POSTGRES_DATABASE"],
            schema: str = os.environ["POSTGRES_SCHEMA"],
    ):

        # try reading secrets from file (if valid path) else use values as secrets
        self.host = self._read_secret(host)
        self.port = self._read_secret(port)
        self.username = self._read_secret(username)
        self.password = self._read_secret(password)
        self.db_name = db_name
        self.schema = schema

        self._initialize_enums()
        self._initialize_custom_functions()

    @staticmethod
    def _read_secret(secret_or_secret_path: str):
        """Read secret (if given value is a filepath, read that file; otherwise, use value as secret)"""
        try:
            # value is path to secret
            return Path(secret_or_secret_path).read_text().strip()
        except FileNotFoundError:
            # value is secret itself, not path to secret
            return secret_or_secret_path

    @staticmethod
    def _load_query_by_name(query_name: str) -> LiteralString:
        """Load a SQL query from a file by name."""
        with open(
                os.path.join(os.path.dirname(__file__), f"sql/{query_name}.sql"),
                mode="r",
                encoding="utf-8",
        ) as query_file:
            return query_file.read()

    def _initialize_connection(self) -> Connection:
        """Initialize a connection to the database."""
        return psycopg.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            dbname=self.db_name,
            connect_timeout=10,
        )

    def _initialize_custom_functions(self):
        """Initialize custom functions in the database."""
        query = sql.SQL(
            self._load_query_by_name(query_name="define_custom_functions")
        ).format(
            schema=sql.Identifier(self.schema),
            custom_exceptions_table=sql.Identifier(Table.CUSTOM_EXCEPTIONS),
            devices_table=sql.Identifier(Table.DEVICES),
            rentals_table=sql.Identifier(Table.RENTALS),
            reservations_table=sql.Identifier(Table.RESERVATIONS),
        )
        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)

    def _initialize_enums(self):

        for psql_enum_name, python_enum_class in [
            ("device_status", DeviceStatus),
            ("device_type", DeviceType),
            ("hold_item", HoldItem),
            ("location", Location),
            ("payment_method", PaymentMethod),
            ("reservation_status", ReservationStatus),
        ]:
            with self._initialize_connection() as conn:
                enum_info = EnumInfo.fetch(conn, psql_enum_name)
                register_enum(enum_info, conn, python_enum_class)

    def __form_select_all_query(self, table_name: Table) -> sql.Composed:
        """Form a query to select all rows from a table in the database"""
        return (
            sql.SQL("SELECT * FROM {schema}.{table}")
            .format(schema=sql.Identifier(self.schema), table=sql.Identifier(table_name))
        )

    def get_full_inventory(self):
        """Get the full inventory of devices from the database."""
        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(self.__form_select_all_query(table_name=Table.DEVICES))
                return self._fetch_result_data_as_dataframe(cursor)

    def select_available_device_ids(self, device_type: DeviceType, location: Location):
        """Get all available devices of a given type at a given location."""

        select_query = sql.SQL(
            self._load_query_by_name(query_name="get_available_device_ids")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.DEVICES),
            device_type=sql.Literal(device_type.value),
            status=sql.Literal(DeviceStatus.AVAILABLE.value),
            location=sql.Literal(location.value),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(select_query)
                return [row[0] for row in cursor.fetchall()]

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

        query = sql.SQL(
            self._load_query_by_name(query_name="insert_devices" if insert_only else "update_devices")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.DEVICES),
            id=sql.Placeholder(name="id"),
            type=sql.Placeholder(name="type"),
            status=sql.Placeholder(name="status"),
            location=sql.Placeholder(name="location"),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.executemany(
                        query,
                        [
                            {
                                "id": device.id,
                                "type": device.type,
                                "status": device.status,
                                "location": device.location
                            } for device in devices
                        ],
                    )
                except psycopg.errors.UniqueViolation:
                    conn.rollback()
                    raise

    def insert_new_reservation(self, reservation: NewReservation) -> str:
        """Create a reservation in the database."""

        insert_query = sql.SQL(
            self._load_query_by_name(query_name="insert_new_reservation")
        ).format(
            device_type_prefix=sql.Placeholder(name="device_type_prefix"),
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RESERVATIONS),
            date=sql.Placeholder(name="date"),
            device_type=sql.Placeholder(name="device_type"),
            name=sql.Placeholder(name="name"),
            phone_number=sql.Placeholder(name="phone_number"),
            location=sql.Placeholder(name="location"),
            reservation_time=sql.Placeholder(name="reservation_time"),
            status=sql.Placeholder(name="status"),
        )

        # execute the query and return the created reservation ID
        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_query,
                    {
                        "device_type_prefix": reservation.device_type.get_prefix(),
                        "date": reservation.date,
                        "device_type": reservation.device_type,
                        "name": reservation.name,
                        "phone_number": reservation.phone_number,
                        "location": reservation.location,
                        "reservation_time": reservation.reservation_time,
                        "status": ReservationStatus.get_default_reservation_status(device_type=reservation.device_type),
                    }
                )
                result = cursor.fetchall()
        return result[0][0]

    def get_rentals_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
            in_progress_rentals_only: bool = False,
    ):
        """Get all rentals on a given date."""

        select_query = sql.SQL(
            self._load_query_by_name(query_name="get_rentals_on_date")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RENTALS),
            date=sql.Placeholder(),
            device_type=sql.Placeholder(),
            in_progress_only=sql.Placeholder(),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(select_query, (date, device_type, device_type, in_progress_rentals_only))
                return self._fetch_result_data_as_dataframe(cursor)

    def get_number_of_reservations_on_date(
            self,
            date: datetime.date,
            device_type: DeviceType,
            location: Location,
    ) -> pd.DataFrame:
        """Get the number of reservations on a given date."""

        select_query = sql.SQL(
            self._load_query_by_name(query_name="get_number_of_reservations_on_date")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RESERVATIONS),
            date=sql.Placeholder(),
            device_type=sql.Placeholder(),
            location=sql.Placeholder(),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(select_query, (date, device_type, location))
                return self._fetch_result_data_as_dataframe(cursor)


    def get_reservations_on_date(
            self,
            date: datetime.date,
            device_type: Optional[DeviceType] = None,
            exclude_picked_up_reservations: bool = False,
    ) -> pd.DataFrame:
        """Get all reservations on a given date."""

        query_name = (
            "get_not_picked_up_reservations_on_date"
            if exclude_picked_up_reservations
            else "get_reservations_on_date"
        )
        select_query = sql.SQL(
            self._load_query_by_name(query_name=query_name)
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RESERVATIONS),
            date=sql.Placeholder(),
            device_type=sql.Placeholder(),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(select_query, (date, device_type, device_type))
                return self._fetch_result_data_as_dataframe(cursor)

    def add_new_rental(self, new_rental: NewRental):
        """Create a new rental in the database."""

        insert_query = sql.SQL(
            self._load_query_by_name(query_name="insert_new_rental")
        ).format(
            device_id=sql.Placeholder(name="device_id"),
            reservation_id=sql.Placeholder(name="reservation_id"),
            device_type_prefix=sql.Placeholder(name="device_type_prefix"),
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RENTALS),
            date=sql.Placeholder(name="date"),
            device_type=sql.Placeholder(name="device_type"),
            pickup_location=sql.Placeholder(name="pickup_location"),
            pickup_time=sql.Placeholder(name="pickup_time"),
            name=sql.Placeholder(name="name"),
            address=sql.Placeholder(name="address"),
            city=sql.Placeholder(name="city"),
            province=sql.Placeholder(name="province"),
            postal_code=sql.Placeholder(name="postal_code"),
            country=sql.Placeholder(name="country"),
            phone_number=sql.Placeholder(name="phone_number"),
            fee_payment_method=sql.Placeholder(name="fee_payment_method"),
            fee_payment_amount=sql.Placeholder(name="fee_payment_amount"),
            deposit_payment_method=sql.Placeholder(name="deposit_payment_method"),
            deposit_payment_amount=sql.Placeholder(name="deposit_payment_amount"),
            staff_name=sql.Placeholder(name="staff_name"),
            items_left_behind=sql.Placeholder(name="items_left_behind"),
            notes=sql.Placeholder(name="notes"),
            signature=sql.Placeholder(name="signature"),
        )

        update_reservation_query = sql.SQL(
            self._load_query_by_name(query_name="update_reservation_at_rental_start")
        ).format(
            reservation_id=sql.Placeholder(name="reservation_id"),
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RESERVATIONS),
            rental_id=sql.Placeholder(name="rental_id"),
        )

        update_device_query = sql.SQL(
            self._load_query_by_name(query_name="update_device_at_rental_start")
        ).format(
            device_id=sql.Placeholder(name="device_id"),
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.DEVICES),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    insert_query,
                    {
                        "device_id": new_rental.device_id,
                        "reservation_id": new_rental.reservation_id,
                        "device_type_prefix": new_rental.device_type.get_prefix(),
                        "date": new_rental.date,
                        "device_type": new_rental.device_type,
                        "pickup_location": new_rental.pickup_location,
                        "pickup_time": new_rental.pickup_time,
                        "name": new_rental.name,
                        "address": new_rental.address,
                        "city": new_rental.city,
                        "province": new_rental.province,
                        "postal_code": new_rental.postal_code,
                        "country": new_rental.country,
                        "phone_number": new_rental.phone_number,
                        "fee_payment_method": new_rental.fee_payment_method,
                        "fee_payment_amount": new_rental.fee_payment_amount,
                        "deposit_payment_method": new_rental.deposit_payment_method,
                        "deposit_payment_amount": new_rental.deposit_payment_amount,
                        "staff_name": new_rental.staff_name,
                        "items_left_behind": new_rental.items_left_behind,
                        "notes": new_rental.notes,
                        "signature": new_rental.signature,
                    }
                )
                rental_id = cursor.fetchall()[0][0]

                # add rental ID to reservation if there was a reservation
                if new_rental.reservation_id:
                    cursor.execute(
                        update_reservation_query,
                        {
                            "reservation_id": new_rental.reservation_id,
                            "rental_id": rental_id,
                        },
                    )

                # update device status
                cursor.execute(
                    update_device_query,
                    {
                        "device_id": new_rental.device_id,
                    },
                )
        return rental_id

    def change_device_for_rental(self, change_device_info: ChangeDeviceInfo):
        """Change the device for a rental in the database."""

        self.update_devices(
            devices=[
                Device(
                    id=change_device_info.new_device_id,
                    type=change_device_info.device_type,
                    status=DeviceStatus.RENTED,
                    location=change_device_info.location
                ),
                Device(
                    id=change_device_info.old_device_id,
                    type=change_device_info.device_type,
                    status=DeviceStatus.AVAILABLE,
                    location=change_device_info.location,
                )
            ]
        )

        update_rental_device_query = sql.SQL(
            self._load_query_by_name(query_name="update_rental_device")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RENTALS),
            rental_id=sql.Placeholder(name="rental_id"),
            device_id=sql.Placeholder(name="new_device_id"),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    update_rental_device_query,
                    {
                        "rental_id": change_device_info.rental_id,
                        "new_device_id": change_device_info.new_device_id,
                    },
                )

    def complete_rental(self, completed_rental: CompletedRental):
        """Complete a rental in the database."""

        update_rental_query = sql.SQL(
            self._load_query_by_name(query_name="update_rental_on_return")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RENTALS),
            rental_id=sql.Placeholder(name="rental_id"),
            return_location=sql.Placeholder(name="return_location"),
            return_time=sql.Placeholder(name="return_time"),
            return_staff_name=sql.Placeholder(name="return_staff_name"),
            return_signature=sql.Placeholder(name="return_signature"),
        )

        update_reservation_query = sql.SQL(
            self._load_query_by_name(query_name="update_reservation_on_rental_return")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.RESERVATIONS),
            rental_id=sql.Placeholder(name="rental_id"),
        )

        update_device_query = sql.SQL(
            self._load_query_by_name(query_name="update_device_on_rental_return")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.DEVICES),
            device_id=sql.Placeholder(name="device_id"),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    update_rental_query,
                    params={
                        "rental_id": completed_rental.id,
                        "return_location": completed_rental.return_location,
                        "return_time": completed_rental.return_time,
                        "return_staff_name": completed_rental.return_staff_name,
                        "return_signature": completed_rental.return_signature,
                    },
                )
                cursor.execute(
                    update_reservation_query,
                    params={
                        "rental_id": completed_rental.id,
                    },
                )
                cursor.execute(
                    update_device_query,
                    params={
                        "device_id": completed_rental.device_id,
                    },
                )

    def update_devices_location(self, device_ids: List[str], location: Location):
        """Update the location of devices in the database."""

        update_query = sql.SQL(
            self._load_query_by_name(query_name="update_devices_location")
        ).format(
            schema=sql.Identifier(self.schema),
            table=sql.Identifier(Table.DEVICES),
            device_id=sql.Placeholder(name="device_id"),
            location=sql.Placeholder(name="location"),
        )

        with self._initialize_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    update_query,
                    [{"device_id": device_id, "location": location} for device_id in device_ids],
                )

    @staticmethod
    def _fetch_result_data_as_dataframe(cursor) -> pd.DataFrame:
        """Fetch data from a cursor as a pandas DataFrame."""
        result = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        return pd.DataFrame(result, columns=col_names)
