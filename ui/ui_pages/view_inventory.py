import streamlit as st

from common.constants import DeviceType
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.display_utils import display_inventory_table
from ui.src.utils import create_inventory_chart

initialize_page(page_header="Inventory")


def display_no_device_in_inventory_message(device_type: DeviceType):
    """Display a message when there are no devices available."""
    st.warning(
        f"""
        **No {device_type.title()}s in Inventory**:
        
        There are no {device_type}s in the inventory. You can add some in the Manage Inventory page.
        """
    )

# load inventory
data_service = DataService()
full_inventory = data_service.get_full_inventory()
if full_inventory is None:
    st.error("**Error**: Unable to load inventory. Please try again later.")
    st.stop()
scooter_inventory, wheelchair_inventory = full_inventory

# generate and display summary charts
for device, inventory in zip(
        [DeviceType.SCOOTER, DeviceType.WHEELCHAIR],
        [scooter_inventory, wheelchair_inventory]
):
    st.subheader(f"{device.title()} Summary")
    if inventory.empty:
        display_no_device_in_inventory_message(device)
    else:
        inventory_chart = create_inventory_chart(inventory)
        st.plotly_chart(inventory_chart, use_container_width=True, config={'displayModeBar': False})

# divider
st.divider()

# display inventory details
scooter_col, wheelchair_col = st.columns(2)
for device, col, inventory in zip(
        [DeviceType.SCOOTER, DeviceType.WHEELCHAIR],
        [scooter_col, wheelchair_col],
        [scooter_inventory, wheelchair_inventory]
):
    with col:
        st.subheader(f"{device.title()} Details")
        if inventory.empty:
            display_no_device_in_inventory_message(device)
        else:
            display_inventory_table(device, inventory)
