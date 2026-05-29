from datetime import date
from typing import Optional, Union

import pandas as pd
import streamlit as st
from plotly import graph_objects as go

from common.constants import DeviceType, DeviceStatus, Location, ReservationStatus
from common.data_models import Device
from common.utils import get_default_timezone
from ui.src.constants import Colour, Page

TIME_FORMAT_STR = "hh:mm a"


def coerce_pandas_aware_datetime(data: pd.Series) -> pd.Series:
    """Coerce a pandas Series to datetime with timezone awareness."""
    return pd.to_datetime(data, errors="coerce", utc=True).dt.tz_convert(get_default_timezone())


# pylint: disable=too-many-arguments
def display_dual_indicator_chart(
        left_title: str,
        right_title: str,
        left_value: Union[float, int],
        right_value: Union[float, int],
        left_total: Union[float, int],
        right_total: Union[float, int],
        key: str,
):
    """
    Display a dual indicator chart with left and right indicators.

    Args:
        left_title (str): The title of the left indicator
        right_title (str): The title of the right indicator
        left_value (Union[float, int]): The value of the left indicator
        right_value (Union[float, int]): The value of the right indicator
        left_total (Union[float, int]): The total value of the left indicator
        right_total (Union[float, int]): The total value of the right indicator
        key (str): The key for the Streamlit component
    """
    fig = go.Figure()
    if left_value < 0.3 * left_total:
        left_colour = Colour.INDICATOR_RED
    elif left_value < left_total:
        left_colour = Colour.INDICATOR_ORANGE
    else:
        left_colour = Colour.INDICATOR_GREEN
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=left_value,
            title={"text": left_title, "font": {"size": 14}},
            domain={'row': 0, 'column': 0},
            number={'suffix': f" / {left_total}"},
            gauge={
                'axis': {'range': [-left_total * 0.03, left_total], 'visible': False},
                'bar': {'color': left_colour},
            },
        ),
    )
    if right_value < 0.3 * right_total:
        right_colour = Colour.INDICATOR_RED
    elif right_value < right_total:
        right_colour = Colour.INDICATOR_ORANGE
    else:
        right_colour = Colour.INDICATOR_GREEN
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=right_value,
            title={"text": right_title, "font": {"size": 14}},
            domain={'row': 0, 'column': 1},
            number={'suffix': f" / {right_total}"},
            gauge={
                'axis': {'range': [-right_total * 0.03, right_total], 'visible': False},
                'bar': {'color': right_colour},
            },
        ),
    )
    fig.update_layout(height=75, margin={"t": 20, "b": 0, "l": 2, "r": 2}, grid={"rows": 1, "columns": 2})
    st.plotly_chart(fig, key=key, use_container_width=True, config={'displayModeBar': False})


def display_dual_indicator_reservation_chart(reservations: pd.DataFrame, location: Location):
    """
    Display a dual indicator chart for reservations at a given location.
    The left indicator is for scooters and the right indicator is for wheelchairs.

    Args:
        reservations (pd.DataFrame): The reservations data.
        location (Location): The location to filter reservations by.
    """
    if reservations.empty:
        st.warning(f":material/warning: No reservations at {location} today")
        return
    location_reservations = reservations[reservations['location'] == location]
    if location_reservations.empty:
        st.warning(f":material/warning: No reservations at {location} today")
        return
    display_dual_indicator_chart(
        left_title=DeviceType.SCOOTER,
        right_title=DeviceType.WHEELCHAIR,
        left_value=len(
            location_reservations[
                (location_reservations['device_type'] == DeviceType.SCOOTER)
                & location_reservations['status'].isin({ReservationStatus.PICKED_UP, ReservationStatus.COMPLETED})
                ]
        ),
        right_value=len(
            location_reservations[
                (location_reservations['device_type'] == DeviceType.WHEELCHAIR)
                & location_reservations['status'].isin({ReservationStatus.PICKED_UP, ReservationStatus.COMPLETED})
                ]
        ),
        left_total=len(
            location_reservations[
                (location_reservations['device_type'] == DeviceType.SCOOTER)
                & ~location_reservations['status'].isin({ReservationStatus.CANCELLED, ReservationStatus.WAITLISTED})
                ]
        ),
        right_total=len(
            location_reservations[
                (location_reservations['device_type'] == DeviceType.WHEELCHAIR)
                & ~location_reservations['status'].isin({ReservationStatus.CANCELLED, ReservationStatus.WAITLISTED})
                ]
        ),
        key=f"{location.value.lower()}_reservations_chart",
    )
    st.caption("Picked Up / Total Reservations")


def display_dual_indicator_rental_chart(rentals: pd.DataFrame, location: Location):
    """
    Display a dual indicator chart for rentals at a given location.
    The left indicator is for scooters and the right indicator is for wheelchairs.

    Args:
        rentals (pd.DataFrame): The rentals data.
        location (Location): The location to filter rentals by.
    """
    if rentals.empty:
        st.warning(f":material/warning: No rentals at {location} today")
        return
    location_rentals = rentals[rentals['pickup_location'] == location]
    if location_rentals.empty:
        st.warning(f":material/warning: No rentals at {location} today")
        return
    display_dual_indicator_chart(
        left_title=DeviceType.SCOOTER,
        right_title=DeviceType.WHEELCHAIR,
        left_value=len(
            location_rentals[
                (location_rentals['device_type'] == DeviceType.SCOOTER)
                & location_rentals['return_time'].notna()
                ]
        ),
        right_value=len(
            location_rentals[
                (location_rentals['device_type'] == DeviceType.WHEELCHAIR)
                & location_rentals['return_time'].notna()
                ]
        ),
        left_total=len(location_rentals[location_rentals['device_type'] == DeviceType.SCOOTER]),
        right_total=len(location_rentals[location_rentals['device_type'] == DeviceType.WHEELCHAIR]),
        key=f"{location.value.lower()}_rentals_chart",
    )
    st.caption("Completed / Total Rentals")


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
            "reservation_time": st.column_config.DatetimeColumn(label="Time", format=TIME_FORMAT_STR),
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
            "pickup_time": st.column_config.DatetimeColumn(label="Pickup Time", format=TIME_FORMAT_STR),
            "deposit_payment_method": st.column_config.TextColumn(label="Deposit Method"),
            "return_location": st.column_config.TextColumn(label="Return Location"),
            "return_time": st.column_config.DatetimeColumn(label="Return Time", format=TIME_FORMAT_STR),
            "items_left_behind": st.column_config.ListColumn(label="Items Left Behind"),
            "notes": st.column_config.TextColumn(label="Notes"),
        },
        column_order=[
            "id", "name", "phone_number", "device_id", "pickup_location", "pickup_time", "deposit_payment_method",
            "return_location", "return_time", "items_left_behind", "notes"
        ],
        use_container_width=True,
    )


def display_rentals_or_reservations_on_date(view_date: date, rentals_or_reservations: Optional[pd.DataFrame],
                                            page: Page):
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
