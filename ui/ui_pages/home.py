import streamlit as st

from common.constants import DeviceType
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.display_utils import display_reservations_table, display_rentals_table

initialize_page()
data_service = DataService()
st.header("Welcome!")

data_to_display = ["Reservations", "Rentals"]
for tab, data_type, get_data_func, display_data_func in zip(
        st.tabs([f"Today's {x}" for x in data_to_display]),
        data_to_display,
        [data_service.get_reservations_on_date, data_service.get_rentals_on_date],
        [display_reservations_table, display_rentals_table],
):
    with tab:
        data = get_data_func(CNEDates.get_default_date())
        if data is None or data.empty:
            st.warning(
                f"**No {data_type} Today**: There are no {data_type.lower()} for "
                f"{CNEDates.get_default_date().strftime('%b %d, %Y')}."
            )
        else:
            for device_type in DeviceType:
                st.subheader(f"{device_type} {data_type}")
                display_data_func(data, device_type=device_type)
