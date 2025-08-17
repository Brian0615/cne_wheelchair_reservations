from datetime import date

import pandas as pd
import streamlit as st

from common.constants import DeviceType, DeviceStatus, Location
from common.data_models import Device
from common.utils import get_default_timezone
from ui.src.constants import Colour, Page

# silence the SettingWithCopyWarning
pd.options.mode.chained_assignment = None  # default='warn'


def coerce_pandas_aware_datetime(data: pd.Series) -> pd.Series:
    """Coerce a pandas Series to datetime with timezone awareness."""
    return pd.to_datetime(data, errors="coerce", utc=True).dt.tz_convert(get_default_timezone())


# pylint: disable=unsubscriptable-object
def display_inventory_table(device_type: DeviceType, inventory: pd.DataFrame):
    """Display the inventory of a device type."""

    status_filter_col, location_filter_col = st.columns(2)
    with status_filter_col:
        status_filter = st.selectbox(
            "Filter by Status",
            options=DeviceStatus,
            index=None,
            key=f"{device_type.value.lower()}_status_filter",
        )
    with location_filter_col:
        location_filter = st.selectbox(
            "Filter by Location",
            options=Location,
            index=None,
            key=f"{device_type.value.lower()}_location_filter",
        )
    if status_filter:
        inventory = inventory[inventory["status"] == status_filter]
    if location_filter:
        inventory = inventory[inventory["location"] == location_filter]

    st.dataframe(
        data=inventory,
        column_order=["id", "status", "location"],
        column_config={
            "id": st.column_config.TextColumn(label=Device.model_fields["id"].title),
            "status": st.column_config.TextColumn(label=Device.model_fields["status"].title),
            "location": st.column_config.TextColumn(label=Device.model_fields["location"].title),
        },
        use_container_width=True,
        hide_index=True,
        key=f"{device_type.value.lower()}_inventory_table",
    )


def display_reservations_table(reservations: pd.DataFrame, device_type: DeviceType):
    """Display the reservations on the UI."""

    # filter for reservations of the right type
    reservations = reservations[reservations["device_type"] == device_type]
    if reservations.empty:
        st.warning(f"**No {device_type} Reservations**: There are no reservations for {device_type.value}s.")
        return

    # Note: utc=True to force tz-aware timestamps
    reservations["reservation_time"] = coerce_pandas_aware_datetime(reservations["reservation_time"])

    # remove tel: prefix from phone numbers
    reservations["phone_number"] = reservations["phone_number"].str.replace(r"^tel:", "", regex=True)

    # turn into styler
    reservations_styler = reservations.set_index("id").style
    reservations_styler = reservations_styler.applymap(
        lambda value: f'background-color: {Colour.get_reservation_table_status_colour(value)}',
        subset=["status"],
    )

    # display reservations
    st.dataframe(
        data=reservations_styler,
        column_config={
            "id": st.column_config.TextColumn(label="ID"),
            "name": st.column_config.TextColumn(label="Name"),
            "phone_number": st.column_config.TextColumn(label="Phone Number"),
            "location": st.column_config.TextColumn(label="Location"),
            "reservation_time": st.column_config.DatetimeColumn(label="Time", format="hh:mm a"),
            "status": st.column_config.TextColumn(label="Status"),
            "rental_id": st.column_config.TextColumn(label="Rental ID"),
            "notes": st.column_config.TextColumn(label="Notes"),
        },
        column_order=["id", "name", "phone_number", "location", "reservation_time", "status", "rental_id", "notes"],
        use_container_width=True,
    )


def display_rentals_table(rentals: pd.DataFrame, device_type: DeviceType):
    """Display the rentals on the UI."""
    rentals = rentals[rentals["device_type"] == device_type]
    if rentals.empty:
        st.warning(f"**No {device_type} Rentals**: There are no rentals for {device_type.value}s.")
        return

    # Note: utc=True to force tz-aware timestamps
    for time_col in ["pickup_time", "return_time"]:
        rentals[time_col] = coerce_pandas_aware_datetime(rentals[time_col])

    # remove tel: prefix from phone numbers
    rentals["phone_number"] = rentals["phone_number"].str.replace(r"^tel:", "", regex=True)

    device_id_label = f"{DeviceType.get_short_label(device_type)} ID"

    # display rentals
    st.dataframe(
        data=rentals.set_index("id"),
        column_config={
            "id": st.column_config.TextColumn(label="ID"),
            "name": st.column_config.TextColumn(label="Name"),
            "phone_number": st.column_config.TextColumn(label="Phone Number"),
            "device_id": st.column_config.TextColumn(label=device_id_label, width="small"),
            "pickup_location": st.column_config.TextColumn(label="Pickup Location"),
            "pickup_time": st.column_config.DatetimeColumn(label="Pickup Time", format="hh:mm a"),
            "deposit_payment_method": st.column_config.TextColumn(label="Deposit Method"),
            "return_location": st.column_config.TextColumn(label="Return Location"),
            "return_time": st.column_config.DatetimeColumn(label="Return Time", format="hh:mm a"),
            "items_left_behind": st.column_config.ListColumn(label="Items Left Behind"),
            "notes": st.column_config.TextColumn(label="Notes"),
        },
        column_order=[
            "id", "name", "phone_number", "device_id", "pickup_location", "pickup_time", "deposit_payment_method",
            "return_location", "return_time", "items_left_behind", "notes"
        ],
        use_container_width=True,
    )


def display_rentals_or_reservations_on_date(view_date: date, rentals_or_reservations: pd.DataFrame, page: Page):
    """Display rentals or reservations for a given page."""
    if page not in {Page.VIEW_RENTALS, Page.VIEW_RESERVATIONS}:
        raise ValueError(f"display_rentals_or_reservations is not supported for this page: {page}")
    page_description_str = page.lstrip("view_")
    display_func = display_rentals_table if page == Page.VIEW_RENTALS else display_reservations_table

    if rentals_or_reservations is None or rentals_or_reservations.empty:
        st.warning(
            f"**No {page_description_str.title()}**: "
            f"There are no {page_description_str} for {view_date.strftime('%b %d, %Y')}."
        )
        return

    for device_type in DeviceType:
        st.subheader(f"{device_type} {page_description_str.title()}")
        display_func(rentals_or_reservations, device_type=device_type)
