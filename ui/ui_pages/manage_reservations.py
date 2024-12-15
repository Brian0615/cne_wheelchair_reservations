import streamlit as st

from common.constants import DeviceType
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.utils import display_reservations, get_date_input

initialize_page(page_header="Manage Reservations")

# initialize data service
data_service = DataService()

view_date = get_date_input(label="View Reservations for:")
reservations = data_service.get_reservations_on_date(date=view_date)
if reservations.empty:
    st.warning(f"**No Reservations**: There are no reservations for {view_date.strftime('%b %d, %Y')}.")
    st.stop()

scooter_reservations, wheelchair_reservations = (
    reservations[reservations["device_type"] == DeviceType.SCOOTER],
    reservations[reservations["device_type"] == DeviceType.WHEELCHAIR],
)
st.subheader(f"{DeviceType.SCOOTER} Reservations")
display_reservations(scooter_reservations, device_type=DeviceType.SCOOTER, admin_mode=True)
st.subheader(f"{DeviceType.WHEELCHAIR} Reservations")
display_reservations(wheelchair_reservations, device_type=DeviceType.WHEELCHAIR, admin_mode=True)
