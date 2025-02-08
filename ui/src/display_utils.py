from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

from common.constants import DeviceType, DeviceStatus, Location, ReservationStatus, PaymentMethod
from common.data_models import Device
from common.utils import get_default_timezone
from ui.src.constants import Page


def display_inventory_table(
        device_type: DeviceType,
        inventory: pd.DataFrame,
        show_filters: bool = True,
) -> pd.DataFrame:
    """Display the inventory of a device type."""

    if show_filters:
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=DeviceStatus,
                key=f"{device_type.value.lower()}_status_filter",
            )
        with col2:
            location_filter = st.selectbox(
                "Filter by Location",
                options=Location,
                index=None,
                key=f"{device_type.value.lower()}_location_filter",
            )
        if status_filter:
            inventory = inventory[inventory["status"].isin(status_filter)]
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
    )


def display_reservations_table(
        reservations: pd.DataFrame,
        device_type: DeviceType,
        admin_mode: bool = False,
) -> Optional[pd.DataFrame]:
    """Display the reservations on the UI."""

    # filter for reservations of the right type
    if reservations.empty:
        st.warning(f"**No {device_type} Reservations**: There are no reservations for {device_type.value}s.")
        return None

    # Note: utc=True to force tz-aware timestamps
    reservations["reservation_time"] = pd.to_datetime(reservations["reservation_time"], errors="coerce", utc=True)
    reservations["reservation_time"] = reservations["reservation_time"].dt.tz_convert(get_default_timezone())

    # display reservations
    updated_reservations = st.data_editor(
        data=reservations.set_index("id"),
        column_config={
            "id": st.column_config.TextColumn(label="ID", required=True, disabled=True),
            "date": None,
            "device_type": None,
            "name": st.column_config.TextColumn(label="Name", required=True, disabled=not admin_mode),
            "phone_number": st.column_config.TextColumn(label="Phone Number", required=True, disabled=not admin_mode),
            "location": st.column_config.SelectboxColumn(
                label="Location",
                options=Location,
                width="small",
                required=True,
                disabled=not admin_mode,
            ),
            "reservation_time": st.column_config.DatetimeColumn(
                label="Time",
                width="small",
                format="hh:mm a",
                required=True,
                disabled=not admin_mode,
            ),
            "status": st.column_config.SelectboxColumn(
                label="Status",
                options=ReservationStatus,
                width="medium",
                required=True,
                disabled=not admin_mode
            ),
            "rental_id": st.column_config.TextColumn(label="Rental ID", required=True, disabled=True),
            "notes": st.column_config.TextColumn(label="Notes", width="medium", disabled=not admin_mode),

        },
        use_container_width=True,
    )
    updated_reservations["reservation_time"] = (
        updated_reservations["reservation_time"].dt.tz_convert(get_default_timezone())
    )
    return updated_reservations


def display_rentals_table(rentals: pd.DataFrame, device_type: DeviceType):
    """Display the rentals on the UI."""
    if rentals.empty:
        st.warning(f"**No {device_type} Rentals**: There are no rentals for {device_type.value}s.")
        return

    # Note: utc=True to force tz-aware timestamps
    for time_col in ["pickup_time", "return_time"]:
        rentals[time_col] = pd.to_datetime(rentals[time_col], errors="coerce", utc=True)  # utc=True to force tz-aware
        rentals[time_col] = rentals[time_col].dt.tz_convert(get_default_timezone())

    device_id_label = f"{DeviceType.get_short_label(device_type)} ID"

    # display rentals
    st.dataframe(
        data=rentals.set_index("id"),
        column_config={
            "id": st.column_config.TextColumn(label="ID"),
            "date": None,
            "device_type": None,
            "name": st.column_config.TextColumn(label="Name", width="medium"),
            "phone_number": st.column_config.TextColumn(label="Phone Number"),
            "device_id": st.column_config.TextColumn(label=device_id_label, width="small"),
            "pickup_location": st.column_config.SelectboxColumn(label="Pickup Location", options=Location),
            "pickup_time": st.column_config.TimeColumn(label="Pickup Time", format="hh:mm a"),
            "deposit_payment_method": st.column_config.SelectboxColumn(label="Deposit Method", options=PaymentMethod),
            "return_location": st.column_config.SelectboxColumn(label="Return Location", options=Location),
            "return_time": st.column_config.TimeColumn(label="Return Time", format="hh:mm a"),
            "items_left_behind": st.column_config.ListColumn(label="Items Left Behind"),
            "notes": st.column_config.TextColumn(label="Notes"),
        },
    )


def display_rentals_or_reservations_on_date(
        view_date: date,
        rentals_or_reservations: pd.DataFrame,
        page: Page,
):
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

    scooter_rentals_or_reservations, wheelchair_rentals_or_reservations = (
        rentals_or_reservations[rentals_or_reservations["device_type"] == DeviceType.SCOOTER],
        rentals_or_reservations[rentals_or_reservations["device_type"] == DeviceType.WHEELCHAIR],
    )
    st.subheader(f"{DeviceType.SCOOTER} {page_description_str.title()}")
    display_func(scooter_rentals_or_reservations, device_type=DeviceType.SCOOTER)
    st.subheader(f"{DeviceType.WHEELCHAIR} {page_description_str.title()}")
    display_func(wheelchair_rentals_or_reservations, device_type=DeviceType.WHEELCHAIR)
