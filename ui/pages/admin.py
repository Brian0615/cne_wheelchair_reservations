from typing import List

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from common.constants import DeviceType
from common.data_models.device import Device
from ui.src.data_service import DataService
from ui.src.utils import display_admin_inventory, admin_add_scooters, admin_add_wheelchairs, transfer_devices

st.set_page_config(layout="wide")
data_service = DataService()


@st.dialog("Transfer Scooters")
def transfer_scooters(scooter_ids: List[str]):
    transfer_devices(data_service, DeviceType.SCOOTER, scooter_ids)


@st.dialog("Transfer Wheelchairs")
def transfer_wheelchairs(wheelchair_ids: List[str]):
    transfer_devices(data_service, DeviceType.WHEELCHAIR, wheelchair_ids)


# display possible success messages
if st.session_state.get("transfer_devices_toast_msg"):
    st.toast(st.session_state["transfer_devices_toast_msg"])
    del st.session_state["transfer_devices_toast_msg"]

st.header("Admin Options")
inventory_tab, = st.tabs(["Inventory"])

with inventory_tab:
    st.info(
        """
        **Use this tab to view and manage the Wheelchair and Scooter inventory.**
        """
    )
    with st.expander("Notes"):
        st.markdown(
            """
            * Any **added** scooters or wheelchairs will default to being **Available**, at **BLC**.
            * Any changes will not be updated until the **Update Inventory** button is clicked.
            * After updating, you may need to refresh the page to see the new changes.
            """
        )

    inventory = data_service.get_full_inventory()
    if inventory.empty:
        inventory = pd.DataFrame(data={field: [] for field in Device.model_fields}, dtype=str)
    inventory = inventory.sort_values(by="id", ascending=True).reset_index(drop=True)
    scooter_inventory = inventory[inventory["type"] == DeviceType.SCOOTER]
    wheelchair_inventory = inventory[inventory["type"] == DeviceType.WHEELCHAIR]

    scooter_col, wheelchair_col = st.columns(2)
    with scooter_col:
        st.subheader("Scooter Inventory")
        add_col, transfer_col = st.columns(2)
        with add_col:
            add_scooters_clicked = st.button("Add Scooters", use_container_width=True)
            if add_scooters_clicked:
                admin_add_scooters(data_service=data_service, scooter_inventory=scooter_inventory)
        with transfer_col:
            st.button(
                label="Transfer Scooters",
                use_container_width=True,
                on_click=transfer_scooters,
                args=(scooter_inventory["id"].tolist(),),
            )
        updated_scooter_inventory = display_admin_inventory(
            device_type=DeviceType.SCOOTER,
            inventory=scooter_inventory,
        )
    with wheelchair_col:
        st.subheader("Wheelchair Inventory")
        add_col, transfer_col = st.columns(2)
        with add_col:
            add_wheelchairs_clicked = st.button("Add Wheelchairs", use_container_width=True)
            if add_wheelchairs_clicked:
                admin_add_wheelchairs(data_service=data_service, wheelchair_inventory=wheelchair_inventory)
        with transfer_col:
            st.button(
                label="Transfer Wheelchairs",
                use_container_width=True,
                on_click=transfer_wheelchairs,
                args=(wheelchair_inventory["id"].tolist(),),
            )
        updated_wheelchair_inventory = display_admin_inventory(
            device_type=DeviceType.WHEELCHAIR,
            inventory=wheelchair_inventory,
        )

    if (
            not scooter_inventory.equals(updated_scooter_inventory)
            or not wheelchair_inventory.equals(updated_wheelchair_inventory)
    ):
        with st.spinner("Updating inventory..."):
            updated_inventory = pd.concat([updated_wheelchair_inventory, updated_scooter_inventory])
            try:
                updated_inventory = [Device(**device) for _, device in updated_inventory.iterrows()]
            except ValidationError as exc:
                st.error(
                    f"**Update Failed**: Inventory update failed due to an error in the provided data. Details below: "
                    f"\n\n"
                    f"{exc}"
                )
                st.stop()
            status_code, details = data_service.update_inventory(updated_inventory)

        match status_code:
            case 200:
                pass
            case 422:
                st.error(
                    f"**Update Failed**: Inventory update failed due to an error in the provided data. Details below: "
                    f"\n\n"
                    f"{details}"
                )
            case _:
                st.error(f"**Update Failed**: Inventory update failed with the following error: {details}")
