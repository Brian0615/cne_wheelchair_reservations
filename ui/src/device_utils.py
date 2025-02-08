import pandas as pd
import streamlit as st

from common.constants import DeviceType, DeviceStatus, Location
from common.data_models import Device
from ui.src.data_service import DataService


def get_manage_devices_str(action: str, device_type: DeviceType, num_devices: int) -> str:
    """Get the string for labelling UI components related to managing devices"""
    return f"{action.title()} {num_devices} {device_type.value}{'s' if abs(num_devices) != 1 else ''}"


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
        if status_code == 200:
            st.session_state["manage_inventory_toast_msg"] = (
                f"**Success!** {label.replace('Add', 'Added')} to the inventory"
            )
            st.rerun()
        else:
            st.error(result)


def update_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Update device status in the inventory."""
    devices_to_update = st.multiselect(
        f"{device_type}s to Update",
        options=sorted(inventory["id"].tolist()),
        default=None,
        key=f"{device_type.value.lower()}_to_update",
    )
    new_status = st.selectbox(
        label="New Status",
        options=DeviceStatus,
        index=None,
        key=f"{device_type.value.lower()}_new_status",
    )

    label = get_manage_devices_str(action="update", device_type=device_type, num_devices=len(devices_to_update))
    if st.button(label=label, disabled=(not devices_to_update or not new_status)):
        status_code, result = data_service.update_devices_status(
            device_ids=devices_to_update,
            status=new_status,
        )
        if status_code == 200:
            st.session_state["manage_inventory_toast_msg"] = (
                f"**Success!** {label.replace('Update', 'Updated')} to {new_status}"
            )
            st.rerun()
        else:
            st.error(result)


def transfer_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Transfer devices to a new location."""
    devices_to_transfer = st.multiselect(
        f"{device_type}s to Transfer",
        options=sorted(inventory["id"].tolist()),
        default=None,
        key=f"{device_type.value.lower()}_to_transfer",
    )
    new_location = st.selectbox(
        label="New Location",
        options=Location,
        index=None,
        key=f"{device_type.value.lower()}_new_location",
    )

    label = get_manage_devices_str(action="transfer", device_type=device_type, num_devices=len(devices_to_transfer))
    if st.button(label=label, disabled=(not devices_to_transfer or not new_location)):
        status_code, result = data_service.update_devices_location(
            device_ids=devices_to_transfer,
            location=new_location,
        )
        if status_code == 200:
            st.session_state["manage_inventory_toast_msg"] = (
                f"**Success!** {label.replace('Transfer', 'Transferred')} to {new_location}"
            )
            st.rerun()
        else:
            st.error(result)


def remove_devices(data_service: DataService, device_type: DeviceType, inventory: pd.DataFrame):
    """Remove devices from the inventory."""
    devices_to_remove = st.multiselect(
        f"{device_type}s to Remove",
        options=sorted(inventory["id"].tolist()),
        default=None,
        key=f"{device_type.value.lower()}_to_remove",
    )

    if devices_to_remove:
        st.warning("**Note**: This action cannot be undone!")
    label = get_manage_devices_str(action="remove", device_type=device_type, num_devices=len(devices_to_remove))
    if st.button(label=label, disabled=not devices_to_remove):
        status_code, result = data_service.remove_devices(device_ids=devices_to_remove)
        if status_code == 200:
            st.session_state["manage_inventory_toast_msg"] = (
                f"**Success!** {label.replace('Remove', 'Removed')} from the inventory"
            )
            st.rerun()
        else:
            st.error(result)
