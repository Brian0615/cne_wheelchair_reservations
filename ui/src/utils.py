import base64
import io
import math
from datetime import datetime, time, date
from typing import List, Optional

import pandas as pd
import streamlit as st
from PIL import Image
from plotly import graph_objects as go
from pydantic import BaseModel

from common.constants import DeviceStatus, DeviceType, Location
from common.data_models.device import Device
from common.utils import get_default_timezone
from ui.src.constants import CNEDates
from ui.src.data_service import DataService


def decode_signature_base64(signature_bytes: bytes) -> Image:
    """Decode a base64 encoded signature."""
    return Image.open(io.BytesIO(base64.b64decode(signature_bytes)))


def encode_signature_base64(signature: Image) -> bytes:
    """Encode a signature as base64."""
    signature_bytes = io.BytesIO()
    signature.save(signature_bytes, format="PNG")
    return base64.b64encode(signature_bytes.getvalue())


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
    all_dates = CNEDates.get_cne_date_list()
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

    # noinspection PyShadowingNames
    @st.cache_data(ttl=30, show_spinner=False)
    def get_rentals_on_date_helper(rental_date: date, in_progress_rentals_only: bool):
        """Helper function to get rentals, for caching purposes"""
        return data_service.get_rentals_on_date(
            rental_date=rental_date,
            in_progress_rentals_only=in_progress_rentals_only,
        )

    col1, col2 = st.columns([1, 2])
    rental_date = get_date_input(label="Rental Date", col=col1)
    rentals = get_rentals_on_date_helper(rental_date=rental_date, in_progress_rentals_only=in_progress_rentals_only)
    if rentals.empty:
        st.warning(f"**No Rentals Today**: There are no rentals on {rental_date.strftime('%b %d, %Y')}.")
        st.stop()

    rental_id = col2.selectbox(
        label="Select a Rental",
        options=sorted(rentals["device_id"] + " - " + rentals["name"] + " (Rental ID: " + rentals["id"] + ")"),
        index=None,
    )
    rental_id = rental_id.split("Rental ID: ")[1][:-1] if rental_id else None
    if not rental_id:
        st.stop()
    return rental_date, rental_id, rentals.loc[rentals["id"] == rental_id].to_dict(orient="records")[0]


def clear_session_state_for_form(
        clear_prefixes: List[str],
        default_date: Optional[date] = None,
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
