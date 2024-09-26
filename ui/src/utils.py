import math
from datetime import datetime, time
from typing import List

import pandas as pd
import streamlit as st
from plotly import graph_objects as go
from pydantic import BaseModel

from common.constants import DeviceStatus, DeviceType, Location
from common.data_models.device import Device
from ui.src.data_service import DataService


def display_inventory(device_type: DeviceType, inventory: pd.DataFrame):
    """Display the inventory of a device type."""
    st.subheader(f"{device_type} Details")
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


def admin_add_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
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


@st.dialog("Add Scooters")
def admin_add_scooters(data_service: DataService, scooter_inventory: pd.DataFrame):
    """Add scooters to the inventory."""
    return admin_add_devices(data_service, DeviceType.SCOOTER, scooter_inventory)


@st.dialog("Add Wheelchairs")
def admin_add_wheelchairs(data_service: DataService, wheelchair_inventory: pd.DataFrame):
    """Add wheelchairs to the inventory."""
    return admin_add_devices(data_service, DeviceType.WHEELCHAIR, wheelchair_inventory)


def display_admin_inventory(device_type: str, inventory: pd.DataFrame):
    """Display the inventory of a device type on the admin page."""

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
            ),
            "location": st.column_config.SelectboxColumn(
                label=Device.model_fields["location"].title,
                options=Location,
                default=Location.BLC,
                required=True,
            ),
        },
        hide_index=True,
        num_rows="fixed",
        use_container_width=True,
        key=f"admin_inventory_{device_type.lower()}"
    )
    updated_inventory["type"] = device_type
    return updated_inventory


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
    colour_mapping = {
        DeviceStatus.AVAILABLE: "#49994C",
        DeviceStatus.RENTED: "#E6920B",
        DeviceStatus.OUT_OF_SERVICE: "#D94936",
        DeviceStatus.BACKUP: "#A6A6A6"
    }
    fig = go.Figure()
    num_per_row = 25
    num_rows = math.ceil(len(inventory) / num_per_row)
    fig.update_layout(
        autosize=False,
        width=num_per_row * 50,
        height=70 * num_rows,
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
            -2 * (i // num_per_row) - 1.8
        )
        fig.add_trace(
            go.Scatter(
                x=[x0, x0, x1, x1, x0],
                y=[y0, y1, y1, y0, y0],
                fill="toself",
                fillcolor=colour_mapping[device["status"]],
                line_color=colour_mapping[device["status"]],
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


def display_reservations(reservations: pd.DataFrame, device_type: DeviceType):
    """Display the reservations on the UI."""
    st.subheader(f"{device_type} Reservations")

    # filter for reservations of the right type
    reservations = reservations[reservations["device_type"] == device_type]
    if reservations.empty:
        st.warning(f"**No {device_type} Reservations Today**: There are no reservations for {device_type.value}s.")
        return

    # format datetime to be in EST
    reservations["pickup_time"] = reservations["pickup_time"].dt.tz_convert("America/Toronto").dt.tz_localize(None)

    # display reservations
    st.dataframe(
        data=reservations.set_index("id"),
        column_config={
            "id": st.column_config.TextColumn(label="ID"),
            "date": None,
            "device_type": None,
            "name": st.column_config.TextColumn(label="Name"),
            "phone_number": st.column_config.TextColumn(label="Phone Number"),
            "location": st.column_config.TextColumn(label="Location", width="small"),
            "pickup_time": st.column_config.TimeColumn(label="Reservation Time", format="hh:mm a"),
            "status": st.column_config.TextColumn(label="Status", width="medium"),
            "device_id": st.column_config.TextColumn(label="Assigned Chair"),
            "rental_id": st.column_config.TextColumn(label="Rental ID"),
            "notes": st.column_config.TextColumn(label="Notes", width="medium"),

        },
        use_container_width=True,
    )
