import pandas as pd
import streamlit as st
from pydantic import ValidationError

from common.constants import DeviceType
from common.data_models.device import Device
from ui.src.data_service import DataService
from ui.src.utils import display_inventory_admin

st.set_page_config(layout="wide")
st.header("Admin Options")

data_service = DataService()

inventory_tab, = st.tabs(["Inventory"])

with inventory_tab:
    st.info("""
    **Use this tab to view and manage the Wheelchair and Scooter inventory.**
    
    
    **Notes**: 
     * Any changes will not be updated until the **Update Inventory** button is clicked.
     * After updating, you may need to refresh the page to see the new changes.
    """)

    # with st.form(key="test_form", clear_on_submit=True):
    inventory = data_service.get_full_inventory()
    scooter_inventory = inventory[inventory["type"] == DeviceType.SCOOTER]
    wheelchair_inventory = inventory[inventory["type"] == DeviceType.WHEELCHAIR]

    scooter_col, wheelchair_col = st.columns(2)
    with scooter_col:
        updated_scooter_inventory = display_inventory_admin(
            device_type=DeviceType.SCOOTER,
            inventory=scooter_inventory,
        )
    with wheelchair_col:
        updated_wheelchair_inventory = display_inventory_admin(
            device_type=DeviceType.WHEELCHAIR,
            inventory=wheelchair_inventory,
        )

    is_submitted = st.button(label="Update Inventory")

if is_submitted:
    with st.spinner("Updating inventory..."):
        updated_inventory = pd.concat([updated_wheelchair_inventory, updated_scooter_inventory])
        try:
            updated_inventory = [Device(**device) for _, device in updated_inventory.iterrows()]
        except ValidationError as exc:
            st.error(
                f"**Update Failed**: Inventory update failed due to an error in the provided data. Details below: \n\n"
                f"{exc}"
            )
            st.stop()
        status_code, details = data_service.set_full_inventory(updated_inventory)

    match status_code:
        case 200:
            st.success("**Update Successful**: Inventory has been updated successfully.")
        case 422:
            st.error(
                f"**Update Failed**: Inventory update failed due to an error in the provided data. Details below: \n\n"
                f"{details}"
            )
        case _:
            st.error(f"**Update Failed**: Inventory update failed with the following error: {details}")
