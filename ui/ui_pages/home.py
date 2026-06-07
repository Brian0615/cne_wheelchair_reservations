import streamlit as st

from common.constants import DeviceType, Location
from ui.src.auth_utils import initialize_page
from common.cne_dates import CNEDates
from ui.src.data_service import DataService
from ui.src.display_utils import (
    display_reservations_table,
    display_rentals_table,
    display_dual_indicator_reservation_chart,
    display_dual_indicator_rental_chart,
)

initialize_page()
data_service = DataService()

reservations = data_service.get_reservations_on_date(CNEDates.get_default_date())
rentals = data_service.get_rentals_on_date(CNEDates.get_default_date())

col1, col2, col3, col4 = st.columns(4)
for col, location, colour in zip([col1, col2], Location, ["orange", "violet"]):
    with col:
        with st.container(border=True):
            st.badge(f"{location} Reservations", color=colour)
            display_dual_indicator_reservation_chart(reservations=reservations, location=location)
for col, location, colour in zip([col3, col4], Location, ["orange", "violet"]):
    with col:
        with st.container(border=True):
            st.badge(f"{location} Rentals", color=colour)
            display_dual_indicator_rental_chart(rentals=rentals, location=location)

data_to_display = ["Reservations", "Rentals"]
for tab, data_type, data, display_data_func in zip(
        st.tabs([f"Today's {x}" for x in data_to_display]),
        data_to_display,
        [reservations, rentals],
        [display_reservations_table, display_rentals_table],
):
    with tab:
        if data is None or data.empty:
            st.warning(
                f"**No {data_type} Today**: There are no {data_type.lower()} for "
                f"{CNEDates.get_default_date().strftime('%b %d, %Y')}."
            )
        else:
            for device_type in DeviceType:
                st.subheader(f"{device_type} {data_type}")
                display_data_func(data, device_type=device_type)
