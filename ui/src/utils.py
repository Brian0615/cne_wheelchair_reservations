import base64
import io
import math
from datetime import datetime, time, date as datetime_date
from typing import List, Optional

import pandas as pd
import streamlit as st
from PIL import Image
from plotly import graph_objects as go
from pydantic import BaseModel

from common.constants import DeviceStatus, DeviceType, Location, PaymentMethod, ReservationStatus
from common.data_models.device import Device
from common.utils import get_default_timezone
from ui.src.constants import CNEDates, Page
from ui.src.data_service import DataService


def decode_signature_base64(signature_bytes: bytes) -> Image:
    """Decode a base64 encoded signature."""
    return Image.open(io.BytesIO(base64.b64decode(signature_bytes)))


def encode_signature_base64(signature: Image) -> bytes:
    """Encode a signature as base64."""
    signature_bytes = io.BytesIO()
    signature.save(signature_bytes, format="PNG")
    return base64.b64encode(signature_bytes.getvalue())


def display_inventory(
        device_type: DeviceType,
        inventory: pd.DataFrame,
        admin_mode: bool = False,
) -> pd.DataFrame:
    """Display the inventory of a device type."""

    if not admin_mode:
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

    updated_inventory = st.data_editor(
        data=inventory,
        column_order=["id", "status", "location"],
        column_config={
            "id": st.column_config.TextColumn(label=Device.model_fields["id"].title, required=True, disabled=True),
            "status": st.column_config.SelectboxColumn(
                label=Device.model_fields["status"].title,
                options=DeviceStatus,
                default=DeviceStatus.AVAILABLE,
                required=True,
                disabled=not admin_mode,
            ),
            "location": st.column_config.SelectboxColumn(
                label=Device.model_fields["location"].title,
                options=Location,
                default=Location.BLC,
                required=True,
                disabled=not admin_mode,
            ),
        },
        use_container_width=True,
        hide_index=True,
        key=f"{'admin_' if admin_mode else ''}inventory_{device_type.lower()}"
    )
    updated_inventory["type"] = device_type
    return updated_inventory


def add_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Add devices to the inventory."""
    num_to_add = st.slider(f"Select the number of {device_type}s to add", 1, 50, 1, 1)

    add_clicked = st.button(f"Add {num_to_add} {device_type.value}{'s' if num_to_add > 1 else ''}")
    if add_clicked:
        if inventory.empty:
            next_device_index = 1
        else:
            next_device_index = inventory["id"].str.extract(r"(\d+)")[0].astype(int).max() + 1

        new_devices = [
            Device(
                id=f"{device_type.value[0].upper()}{next_device_index + i:02}",
                type=device_type,
                status=DeviceStatus.AVAILABLE,
                location=Location.BLC,
            )
            for i in range(num_to_add)
        ]

        data_service.add_to_inventory(devices=new_devices)
        st.rerun()


def load_reservations_for_date(date: datetime):
    """Load mock reservations for a given date."""
    reservations = pd.DataFrame(
        data={
            "name": ["Person A", "Person B", "Person C"],
            "phone_number": ["111-222-3333", "444-555-6666", "777-888-9999"],
            "location": ["BLC", "PG", "PG"],
            "reservation_time": [datetime.combine(date.date(), time(10, 15)) for _ in range(3)],
            "notes": ["", "", ""],
            "is_picked_up": [True, False, True],
            "time_out": [datetime.combine(date.date(), time(10, 15)), None, None],
            "time_in": [None, None, None],
        }
    )
    return reservations


# noinspection PyTypeChecker
def create_inventory_chart(inventory: pd.DataFrame):
    """Create a chart to display the inventory."""

    fig = go.Figure()
    num_per_row = 25
    num_rows = math.ceil(len(inventory) / num_per_row)
    fig.update_layout(
        autosize=False,
        width=num_per_row * 50,
        height=35 * num_rows,
        margin={"l": 0, "r": 0, "b": 0, "t": 0, "pad": 0},
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    fig.update_xaxes(range=[0, num_per_row], visible=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-2 * num_rows, 0], visible=False, showgrid=False, zeroline=False)
    for i, (_, device) in enumerate(inventory.iterrows()):
        x0, y0, x1, y1 = (
            i % num_per_row,
            -2 * (i // num_per_row),
            (i % num_per_row) + 0.8,
            -2 * (i // num_per_row) - 1.5
        )
        fig.add_trace(
            go.Scatter(
                x=[x0, x0, x1, x1, x0],
                y=[y0, y1, y1, y0, y0],
                fill="toself",
                fillcolor=DeviceStatus.get_device_status_colour(device["status"]),
                line_color=DeviceStatus.get_device_status_colour(device["status"]),
                mode="lines",
                text=f"<b>{device['id']}</b><br>Status: {device['status']}<br>Location: {device['location']}",
                hoverinfo="text",
                hoverlabel={"font_size": 14},
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[(x0 + x1) / 2.0],
                y=[(y0 + y1) / 2.0],
                mode="text",
                text=device["id"],
                textfont={"color": "#EEEEEE", "size": 14},
                textposition="middle center",
                showlegend=False,
                hoverinfo="skip",
            )
        )
    return fig


def display_validation_errors(errors: List[dict], validation_class: type[BaseModel]):
    """Display validation errors on the UI."""
    display_errors = []
    for error in errors:
        field_name = validation_class.model_fields[error['loc'][0]].title
        if not field_name:
            field_name = error['loc'][0]

        match error['type']:
            case "enum":
                message = error["msg"].replace("Input should be", "Input should be one of:")
            case "string_too_short" | "string_too_long":
                message = error["msg"].replace("String", "Input")
            case _:
                message = error["msg"]
        display_errors.append(f"{field_name}: {message}")

    error_str = "**Validation Error:** There was an error validating the input data. Please check the following fields:"
    error_str = "\n* ".join([error_str] + display_errors)

    st.error(error_str)


def display_reservations(
        reservations: pd.DataFrame,
        device_type: DeviceType,
        admin_mode: bool = False,
) -> Optional[pd.DataFrame]:
    """Display the reservations on the UI."""

    # filter for reservations of the right type
    if reservations.empty:
        st.warning(f"**No {device_type} Reservations**: There are no reservations for {device_type.value}s.")
        return None

    # turn times into naive timestamps
    reservations["reservation_time"] = reservations["reservation_time"].dt.tz_localize(None)

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
            "reservation_time": st.column_config.TimeColumn(
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
        updated_reservations["reservation_time"].dt.tz_localize(get_default_timezone())
    )
    return updated_reservations


def display_rentals(rentals: pd.DataFrame, device_type: DeviceType):
    """Display the rentals on the UI."""
    if rentals.empty:
        st.warning(f"**No {device_type} Rentals**: There are no rentals for {device_type.value}s.")
        return

    # localize timestamps to default timezone then change into naive timestamps
    for time_col in ["pickup_time", "return_time"]:
        rentals[time_col] = pd.to_datetime(rentals[time_col], errors="coerce", utc=True)
        rentals[time_col] = rentals[time_col].dt.tz_convert(get_default_timezone()).dt.tz_localize(None)

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


def transfer_devices(data_service: DataService, device_type: DeviceType, device_ids: List[str]):
    """Transfer devices to a new location."""
    devices_to_transfer = st.multiselect(
        f"{device_type}s to Transfer",
        options=sorted(device_ids),
        default=None,
        key=f"{device_type.value.lower()}_to_transfer",
    )
    new_location = st.selectbox(
        label="New Location",
        options=Location,
        index=None,
        key=f"{device_type.value.lower()}_new_location",
    )

    num_devices_str = f"{len(devices_to_transfer)} {device_type}{'s' if len(devices_to_transfer) > 1 else ''}"
    if st.button(
            label=f"Transfer {num_devices_str}",
            disabled=(not devices_to_transfer or not new_location)
    ):
        status_code, result = data_service.update_devices_location(
            device_ids=devices_to_transfer,
            location=new_location,
        )
        if status_code == 200:
            st.session_state["transfer_devices_toast_msg"] = (
                f"**Success!** Transferred {num_devices_str} to {new_location}"
            )
            st.rerun()
        else:
            st.error(result)


def get_date_input(label: str, col=None):
    """Get a date input with the default date set to today."""
    all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
    if col is None:
        col, _ = st.columns([1, 3])
    return col.date_input(
        label=label,
        value=CNEDates.get_default_date(),
        min_value=all_dates[0],
        max_value=all_dates[-1],
    )


def get_rental_selection(data_service: DataService, in_progress_rentals_only: bool):
    """Render rental retrival options and return the selected rental."""

    col1, col2 = st.columns([1, 2])
    date = get_date_input(label="Rental Date", col=col1)
    rentals = data_service.get_rentals_on_date(date=date, in_progress_rentals_only=in_progress_rentals_only)
    if rentals.empty:
        st.warning(f"**No Rentals Today**: There are no rentals on {date.strftime('%b %d, %Y')}.")
        st.stop()

    rental_id = col2.selectbox(
        label="Select a Rental",
        options=sorted(rentals["device_id"] + " - " + rentals["name"] + " (Rental ID: " + rentals["id"] + ")"),
        index=None,
    )
    rental_id = rental_id.split("Rental ID: ")[1][:-1] if rental_id else None
    if not rental_id:
        st.stop()
    return date, rental_id, rentals.loc[rentals["id"] == rental_id].to_dict(orient="records")[0]


def display_rentals_or_reservations_on_date(
        view_date: datetime_date,
        rentals_or_reservations: pd.DataFrame,
        page: Page,
):
    """Display rentals or reservations for a given page."""
    if page not in {Page.VIEW_RENTALS, Page.VIEW_RESERVATIONS}:
        raise ValueError(f"display_rentals_or_reservations is not supported for this page: {page}")
    page_description_str = page.lstrip("view_")
    display_func = display_rentals if page == Page.VIEW_RENTALS else display_reservations

    if rentals_or_reservations.empty:
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


def clear_session_state_for_form(
        clear_prefixes: List[str],
        default_date: Optional[datetime_date] = None,
        default_time: Optional[time] = None
):
    """Clear session state data with a given list of prefixes"""
    for key in st.session_state.keys():
        if any(key.startswith(prefix) for prefix in clear_prefixes):
            if key.endswith("date"):
                st.session_state[key] = default_date if default_date is not None else CNEDates.get_default_date()
            elif key.endswith("time"):
                st.session_state[key] = (
                    default_time if default_time is not None else datetime.now(tz=get_default_timezone()).time()
                )
            else:
                st.session_state[key] = None
