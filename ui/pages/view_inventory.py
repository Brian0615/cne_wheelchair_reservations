import streamlit as st

from common.constants import DeviceType
from ui.src.data_service import DataService
from ui.src.utils import display_inventory, create_inventory_chart

# page setup
st.set_page_config(layout="wide")
st.header("Inventory")

# load inventory
data_service = DataService()
scooter_inventory, wheelchair_inventory = data_service.get_full_inventory()

# generate and display summary charts
st.subheader("Scooter Summary")
scooter_inventory_chart = create_inventory_chart(scooter_inventory)
st.plotly_chart(scooter_inventory_chart, use_container_width=True, config={'displayModeBar': False})
st.subheader("Wheelchair Summary")
wheelchair_inventory_chart = create_inventory_chart(wheelchair_inventory)
st.plotly_chart(wheelchair_inventory_chart, use_container_width=True, config={'displayModeBar': False})

# divider
st.divider()

# display inventory details
scooter_col, wheelchair_col = st.columns(2)
with scooter_col:
    st.subheader("Scooter Details")
    display_inventory(DeviceType.SCOOTER, scooter_inventory)
with wheelchair_col:
    st.subheader("Wheelchair Details")
    display_inventory(DeviceType.WHEELCHAIR, wheelchair_inventory)
