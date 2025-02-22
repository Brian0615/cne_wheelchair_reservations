import streamlit as st

from common.constants import DeviceType
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.display_utils import display_reservations_table, display_rentals_table

initialize_page()
data_service = DataService()
st.header("Welcome!")

reservations_tab, rentals_tab = st.tabs(["Reservations", "Rentals"])

with reservations_tab:
    reservations = data_service.get_reservations_on_date(CNEDates.get_default_date())
    if reservations is None or reservations.empty:
        st.warning(
            f"**No Reservations Today**: There are no reservations for "
            f"{CNEDates.get_default_date().strftime('%b %d, %Y')}."
        )
    else:
        scooter_reservations, wheelchair_reservations = (
            reservations[reservations["device_type"] == DeviceType.SCOOTER],
            reservations[reservations["device_type"] == DeviceType.WHEELCHAIR],
        )
        st.subheader(f"Today's {DeviceType.SCOOTER} Reservations")
        display_reservations_table(scooter_reservations, device_type=DeviceType.SCOOTER)
        st.subheader(f"Today's {DeviceType.WHEELCHAIR} Reservations")
        display_reservations_table(wheelchair_reservations, device_type=DeviceType.WHEELCHAIR)

with rentals_tab:
    rentals = data_service.get_rentals_on_date(CNEDates.get_default_date())
    if rentals is None or rentals.empty:
        st.warning(
            f"**No Rentals Today**: There are no rentals for "
            f"{CNEDates.get_default_date().strftime('%b %d, %Y')}."
        )
    else:
        scooter_rentals, wheelchair_rentals = (
            rentals[rentals["device_type"] == DeviceType.SCOOTER],
            rentals[rentals["device_type"] == DeviceType.WHEELCHAIR],
        )
        st.subheader(f"Today's {DeviceType.SCOOTER} Rentals")
        display_rentals_table(scooter_rentals, device_type=DeviceType.SCOOTER)
        st.subheader(f"Today's {DeviceType.WHEELCHAIR} Rentals")
        display_rentals_table(wheelchair_rentals, device_type=DeviceType.WHEELCHAIR)
