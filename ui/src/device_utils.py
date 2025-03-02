from functools import wraps
from typing import List, Tuple

import pandas as pd
import streamlit as st

from common.constants import DeviceType, DeviceStatus, Location
from common.data_models import Device
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
def add_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Add devices to the inventory."""
    num_to_add = st.number_input(f"Number of {device_type}s", 1, 50, 1, 1)

    label = get_manage_devices_str(action="add", device_type=device_type, num_devices=num_to_add)
    if st.button(label=label, disabled=num_to_add < 1):
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
