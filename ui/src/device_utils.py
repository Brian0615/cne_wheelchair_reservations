import itertools
import math
from functools import wraps
from typing import List, Tuple

import pandas as pd
import streamlit as st
from plotly import graph_objects as go

from common.constants import DeviceType, DeviceStatus, Location
from common.data_models import NewDevice
from ui.src.constants import CNEDates
from ui.src.data_service import DataService


def get_manage_devices_str(action: str, device_type: DeviceType, num_devices: int) -> str:
    """Get the string for labelling UI components related to managing devices"""
    return f"{action.title()} {num_devices} {device_type.value}{'s' if abs(num_devices) != 1 else ''}"


def display_devices_multiselect(inventory: pd.DataFrame, device_type: DeviceType, action: str) -> Tuple[List[str], str]:
    """Display a multiselect widget to select devices for management actions."""
    selected_devices = st.multiselect(
        f"{device_type}s to {action.title()}",
        options=sorted(inventory["id"].tolist()),
        default=None,
        key=f"{device_type.value.lower()}_to_{action.lower()}",
    )
    label = get_manage_devices_str(action=action, device_type=device_type, num_devices=len(selected_devices))
    return selected_devices, label


def display_toast_on_success(func):
    """Decorator to display a toast message on successful device management actions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is None:
            return
        status_code, response, success_msg = result
        if status_code == 200:
            st.session_state["manage_inventory_toast_msg"] = f"**Success!** {success_msg}"
            st.rerun()
        else:
            st.error(response)

    return wrapper


@display_toast_on_success
def add_devices(data_service: DataService, device_type: DeviceType):
    """Add devices to the inventory."""

    num_to_add = {}
    cols = st.columns(len(Location))
    for col, location in zip(cols, Location):
        num_to_add[location] = col.number_input(
            f"Number of {device_type}s to add at **{location}**",
            min_value=0,
            max_value=50,
            value=0,
            step=1,
        )

    label = get_manage_devices_str(action="add", device_type=device_type, num_devices=sum(num_to_add.values()))
    if st.button(label=label, disabled=sum(num_to_add.values()) < 1):
        new_devices = itertools.chain.from_iterable(
            [
                NewDevice(
                    cne_year=CNEDates.get_cne_year(),
                    type=device_type,
                    status=DeviceStatus.AVAILABLE,
                    location=Location(location),
                )
            ] * num_to_add_at_location
            for location, num_to_add_at_location in num_to_add.items()
        )

        status_code, result = data_service.add_devices(devices=new_devices)
        return status_code, result, f"{label.replace('Add', 'Added')} to the inventory"
    return None


@display_toast_on_success
def update_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Update device status in the inventory."""
    device_ids, label = display_devices_multiselect(inventory=inventory, device_type=device_type, action="update")
    new_status = st.selectbox(
        label="New Status",
        options=DeviceStatus,
        index=None,
        key=f"{device_type.value.lower()}_new_status",
    )

    if st.button(label=label, disabled=(not device_ids or not new_status)):
        status_code, result = data_service.update_devices_status(device_ids=device_ids, status=new_status)
        return status_code, result, f"{label.replace('Update', 'Updated')} to {new_status}"
    return None


@display_toast_on_success
def transfer_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Transfer devices to a new location."""
    device_ids, label = display_devices_multiselect(inventory=inventory, device_type=device_type, action="transfer")
    new_location = st.selectbox(
        label="New Location",
        options=Location,
        index=None,
        key=f"{device_type.value.lower()}_new_location",
    )

    if st.button(label=label, disabled=(not device_ids or not new_location)):
        status_code, result = data_service.update_devices_location(device_ids=device_ids, location=new_location)
        return status_code, result, f"{label.replace('Transfer', 'Transferred')} to {new_location}"
    return None


@display_toast_on_success
def remove_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Remove devices from the inventory."""
    device_ids, label = display_devices_multiselect(inventory=inventory, device_type=device_type, action="remove")
    if device_ids:
        st.warning("**Note**: This action cannot be undone!")

    if st.button(label=label, disabled=not device_ids):
        status_code, result = data_service.remove_devices(device_ids=device_ids)
        return status_code, result, f"{label.replace('Remove', 'Removed')} from the inventory"
    return None


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
