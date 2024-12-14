import pandas as pd
import streamlit as st

from common.constants import DeviceType
from common.data_models.device import Device
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.utils import display_inventory, add_devices, transfer_devices

initialize_page(page_header="Manage Inventory")
data_service = DataService()


@st.dialog("Add Scooters")
def add_scooters():
    """Add scooters to the inventory."""
    return add_devices(data_service, DeviceType.SCOOTER, st.session_state["admin_scooter_inventory"])


@st.dialog("Add Wheelchairs")
def add_wheelchairs():
    """Add wheelchairs to the inventory."""
    return add_devices(data_service, DeviceType.WHEELCHAIR, st.session_state["admin_wheelchair_inventory"])


@st.dialog("Transfer Scooters")
def transfer_scooters():
    transfer_devices(data_service, DeviceType.SCOOTER, st.session_state["admin_scooter_inventory"]["id"].tolist())


@st.dialog("Transfer Wheelchairs")
def transfer_wheelchairs():
    transfer_devices(data_service, DeviceType.WHEELCHAIR, st.session_state["admin_wheelchair_inventory"]["id"].tolist())


def update_inventory(new_inventory: pd.DataFrame, device_type: DeviceType):
    # find changed rows
    new_inventory = new_inventory.merge(
        right=st.session_state[f"admin_{device_type.lower()}_inventory"],
        suffixes=("", "_original"),
        on="id",
    )
    new_inventory = new_inventory[
        (new_inventory["location"] != new_inventory["location_original"])
        | (new_inventory["status"] != new_inventory["status_original"])
        ]
    new_inventory = new_inventory.drop(columns=[col for col in new_inventory.columns if "_original" in col])
    status_code, details = data_service.update_inventory(
        inventory=[Device(**device) for _, device in new_inventory.iterrows()]
    )
    match status_code:
        case 200:
            st.session_state[f"admin_{device_type.lower()}_inventory"] = new_inventory
            st.rerun()
        case 422:
            st.error(
                f"**Update Failed**: Inventory update failed due to an error in the provided data. Details below: "
                f"\n\n"
                f"{details}"
            )
        case _:
            st.error(f"**Update Failed**: Inventory update failed with the following error: {details}")


# display possible success messages
if st.session_state.get("transfer_devices_toast_msg"):
    st.toast(st.session_state["transfer_devices_toast_msg"])
    del st.session_state["transfer_devices_toast_msg"]

(
    st.session_state["admin_scooter_inventory"],
    st.session_state["admin_wheelchair_inventory"],
) = data_service.get_full_inventory()

scooter_col, wheelchair_col = st.columns(2)
with scooter_col:
    st.subheader("Scooter Inventory")
    add_col, transfer_col = st.columns(2)
    add_col.button(label="Add Scooters", use_container_width=True, on_click=add_scooters)
    transfer_col.button(label="Transfer Scooters", use_container_width=True, on_click=transfer_scooters)

with wheelchair_col:
    st.subheader("Wheelchair Inventory")
    add_col, transfer_col = st.columns(2)
    add_col.button(label="Add Wheelchairs", use_container_width=True, on_click=add_wheelchairs)
    transfer_col.button(label="Transfer Wheelchairs", use_container_width=True, on_click=transfer_wheelchairs)

with scooter_col:
    if st.session_state["admin_scooter_inventory"].empty:
        st.warning(
            """
            **No Scooters in Inventory**:
            
            There are no scooters in the inventory. Add some using the button above.
            """
        )
    else:
        updated_scooter_inventory = display_inventory(
            device_type=DeviceType.SCOOTER,
            inventory=st.session_state["admin_scooter_inventory"],
            admin_mode=True,
        )
        if not st.session_state["admin_scooter_inventory"].equals(updated_scooter_inventory):
            update_inventory(new_inventory=updated_scooter_inventory, device_type=DeviceType.SCOOTER)

with wheelchair_col:
    if st.session_state["admin_wheelchair_inventory"].empty:
        st.warning("""
            **No Wheelchairs in Inventory**:
            
            There are no wheelchairs in the inventory. Add some using the button above.
            """
                   )
    else:
        updated_wheelchair_inventory = display_inventory(
            device_type=DeviceType.WHEELCHAIR,
            inventory=st.session_state["admin_wheelchair_inventory"],
            admin_mode=True,
        )
        if not st.session_state["admin_wheelchair_inventory"].equals(updated_wheelchair_inventory):
            update_inventory(new_inventory=updated_wheelchair_inventory, device_type=DeviceType.WHEELCHAIR)
