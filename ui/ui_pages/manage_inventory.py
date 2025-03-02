import pandas as pd
import streamlit as st

from common.constants import DeviceType
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.device_utils import add_devices, update_devices, transfer_devices, remove_devices
from ui.src.display_utils import display_inventory_table

initialize_page(page_header="Manage Inventory")
data_service = DataService()


def display_no_device_in_inventory_message(device_type: DeviceType):
    """Display a message when there are no devices available."""
    st.warning(
        f"""
        **No {device_type.title()}s**: There are no {device_type}s in the inventory.

        You can add some using the "Add" button above.
        """
    )


@st.dialog("Add Scooters")
def add_scooters(inventory: pd.DataFrame):
    """Add scooters to the inventory."""
    return add_devices(data_service, DeviceType.SCOOTER, inventory)


@st.dialog("Add Wheelchairs")
def add_wheelchairs(inventory: pd.DataFrame):
    """Add wheelchairs to the inventory."""
    return add_devices(data_service, DeviceType.WHEELCHAIR, inventory)


@st.dialog("Update Scooter Status")
def update_scooters(inventory: pd.DataFrame):
    """Update the status of scooters in the inventory."""
    update_devices(data_service, DeviceType.SCOOTER, inventory)


@st.dialog("Update Wheelchair Status")
def update_wheelchairs(inventory: pd.DataFrame):
    """Update the status of wheelchairs in the inventory."""
    update_devices(data_service, DeviceType.WHEELCHAIR, inventory)


@st.dialog("Transfer Scooters")
def transfer_scooters(inventory: pd.DataFrame):
    """Transfer scooters to another location."""
    transfer_devices(data_service, DeviceType.SCOOTER, inventory)


@st.dialog("Transfer Wheelchairs")
def transfer_wheelchairs(inventory: pd.DataFrame):
    """Transfer wheelchairs to another location."""
    transfer_devices(data_service, DeviceType.WHEELCHAIR, inventory)


@st.dialog("Remove Scooters")
def remove_scooters(inventory: pd.DataFrame):
    """Remove scooters from the inventory."""
    remove_devices(data_service, DeviceType.SCOOTER, inventory)


@st.dialog("Remove Wheelchairs")
def remove_wheelchairs(inventory: pd.DataFrame):
    """Remove wheelchairs from the inventory."""
    remove_devices(data_service, DeviceType.WHEELCHAIR, inventory)


# display possible success messages
if st.session_state.get("manage_inventory_toast_msg"):
    st.toast(st.session_state["manage_inventory_toast_msg"])
    del st.session_state["manage_inventory_toast_msg"]

full_inventory = data_service.get_full_inventory()
if full_inventory is None:
    st.error("**Error**: Unable to load inventory. Please try again later.")
    st.stop()
scooter_inventory, wheelchair_inventory = full_inventory


def display_manage_options(device_type: DeviceType):
    """Display the options for managing the inventory."""
    add_col, status_col, transfer_col, remove_col = st.columns(4)
    add_col.button(
        label="Add",
        icon=":material/add_circle:",
        use_container_width=True,
        on_click=add_scooters if device_type == DeviceType.SCOOTER else add_wheelchairs,
        args=(scooter_inventory if device_type == DeviceType.SCOOTER else wheelchair_inventory,),
        key=f"manage_inventory_add_{device_type.lower()}s",
    )
    status_col.button(
        label="Update",
        icon=":material/edit_square:",
        use_container_width=True,
        on_click=update_scooters if device_type == DeviceType.SCOOTER else update_wheelchairs,
        args=(scooter_inventory if device_type == DeviceType.SCOOTER else wheelchair_inventory,),
        key=f"manage_inventory_update_{device_type.lower()}s",
    )
    transfer_col.button(
        label="Transfer",
        icon=":material/drag_pan:",
        use_container_width=True,
        on_click=transfer_scooters if device_type == DeviceType.SCOOTER else transfer_wheelchairs,
        args=(scooter_inventory if device_type == DeviceType.SCOOTER else wheelchair_inventory,),
        key=f"manage_inventory_transfer_{device_type.lower()}s",
    )
    remove_col.button(
        label="Remove",
        icon=":material/delete:",
        use_container_width=True,
        on_click=remove_scooters if device_type == DeviceType.SCOOTER else remove_wheelchairs,
        args=(scooter_inventory if device_type == DeviceType.SCOOTER else wheelchair_inventory,),
        key=f"manage_inventory_remove_{device_type.lower()}s",
    )


scooter_col, wheelchair_col = st.columns(2, gap="large")
for col, device_inventory, device in zip(
        [scooter_col, wheelchair_col],
        [scooter_inventory, wheelchair_inventory],
        [DeviceType.SCOOTER, DeviceType.WHEELCHAIR]
):
    with col:
        st.subheader(f"{device.value} Inventory")
        display_manage_options(device_type=device)

        if device_inventory.empty:
            display_no_device_in_inventory_message(device)
        else:
            display_inventory_table(device_type=device, inventory=device_inventory)
