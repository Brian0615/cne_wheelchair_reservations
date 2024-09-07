# pylint: disable=not-context-manager

import os
from typing import List

import pandas as pd
import psycopg
from psycopg import sql

from api.src.constants import Table
from api.src.exceptions import UniqueViolation
from common.constants import DeviceStatus, DeviceType, Location
from common.data_models.device import Device


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

    def get_available_devices(self, device_type: DeviceType, location: Location):
        """Get all available devices of a given type at a given location."""
        with self.__initialize_handle() as handle:
            with handle.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        """
                        SELECT id FROM {schema}.{table}
                        WHERE type = {device_type} AND status = {status} AND location = {location}
                        """
                    ).format(
                        schema=sql.Identifier(self.schema),
                        table=sql.Identifier(Table.DEVICES),
                        device_type=sql.Literal(device_type.value),
                        status=sql.Literal(DeviceStatus.AVAILABLE.value),
                        location=sql.Literal(location.value),
                    )
                )
                result = cursor.fetchall()
                col_names = [desc[0] for desc in cursor.description]
                return pd.DataFrame(result, columns=col_names)["id"].tolist()

    def add_to_inventory(self, devices: List[Device]):
        """Add devices to the inventory in the database. Will raise an error if there are any conflicts."""
        with self.__initialize_handle() as handle:

            with handle.cursor() as cursor:

                # insert the new data into the table
                insert_query = sql.SQL(
                    """
                    INSERT INTO {schema}.{table} ({fields}) VALUES ({values}) 
                    """
                ).format(
                    schema=sql.Identifier(self.schema),
                    table=sql.Identifier(Table.DEVICES),
                    fields=sql.SQL(", ").join([sql.Identifier(field) for field in Device.model_fields]),
                    values=sql.SQL(", ").join([sql.Placeholder() for _ in Device.model_fields]),
                )

                try:
                    cursor.executemany(
                        insert_query,
                        [(device.id, device.type, device.status, device.location) for device in devices],
                    )
                except psycopg.errors.UniqueViolation as exc:
                    handle.rollback()
                    raise UniqueViolation(exc.diag.message_primary + " - " + exc.diag.message_detail) from exc

    def update_inventory(self, devices: List[Device]):
        """
        Update devices in the database.
        Will insert for any non-existing devices, and overwrite any existing devices
        """
        with self.__initialize_handle() as handle:

            with handle.cursor() as cursor:

                # insert the new data into the table
                insert_query = sql.SQL(
                    """
                    INSERT INTO {schema}.{table} ({fields}) VALUES ({values}) 
                    ON CONFLICT ({key_field}) 
                    DO UPDATE SET 
                        type=EXCLUDED.type, 
                        status=EXCLUDED.status, 
                        location=EXCLUDED.location
                    """
                ).format(
                    schema=sql.Identifier(self.schema),
                    table=sql.Identifier(Table.DEVICES),
                    fields=sql.SQL(", ").join([sql.Identifier(field) for field in Device.model_fields]),
                    values=sql.SQL(", ").join([sql.Placeholder() for _ in Device.model_fields]),
                    key_field=sql.Identifier(Device.get_key_field()),
                    update_set=sql.SQL(", ").join([
                        sql.SQL("{field}=EXCLUDED.{field}").format(field=field)
                        for field in Device.model_fields
                        if field != Device.get_key_field()
                    ])
                )

                try:
                    cursor.executemany(
                        insert_query,
                        [(device.id, device.type, device.status, device.location) for device in devices],
                    )
                except psycopg.errors.UniqueViolation as exc:
                    handle.rollback()
                    raise UniqueViolation(exc.diag.message_primary + " - " + exc.diag.message_detail) from exc
