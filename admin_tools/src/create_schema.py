import os
from typing import LiteralString

import pandas as pd
import psycopg
from psycopg import sql

from common.constants import Table


def load_query_by_name(query_name: str) -> LiteralString:
    """Load a SQL query from a file by name."""
    with open(
            os.path.join(os.path.dirname(__file__), f"sql/{query_name}.sql"),
            mode="r",
            encoding="utf-8",
    ) as query_file:
        return query_file.read()


def create_schema(schema_name: str):
    """Create a new schema in the database."""

    create_schema_query = sql.SQL(
        load_query_by_name("create_schema")
    ).format(
        schema_name=sql.Identifier(schema_name),
        rentals_table=sql.Identifier(Table.RENTALS),
        reservations_table=sql.Identifier(Table.RESERVATIONS),
        devices_table=sql.Identifier(Table.DEVICES),
        custom_exceptions_table=sql.Identifier(Table.CUSTOM_EXCEPTIONS),
    )
    insert_custom_exception_query = sql.SQL(
        load_query_by_name("insert_custom_exception")
    ).format(
        schema_name=sql.Identifier(schema_name),
        custom_exceptions_table=sql.Identifier(Table.CUSTOM_EXCEPTIONS),
        error_code=sql.Placeholder("error_code"),
        error_message=sql.Placeholder("error_message"),
    )
    custom_exceptions = pd.read_csv(os.path.join(os.path.dirname(__file__), "data/custom_exceptions.csv"))

    with psycopg.connect(
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
            user=os.environ["POSTGRES_USERNAME"],
            password=os.environ["POSTGRES_PASSWORD"],
            dbname=os.environ["POSTGRES_DATABASE"],
    ) as conn:
        with conn.cursor() as cursor:
            print(
                f"Connected to PostgreSQL at {os.environ['POSTGRES_HOST']} "
                f"as user {os.environ['POSTGRES_USERNAME']}"
            )
            cursor.execute(create_schema_query)
            cursor.executemany(insert_custom_exception_query, custom_exceptions.to_dict(orient="records"))
            conn.commit()

    print(f"Schema {schema_name} created successfully")
