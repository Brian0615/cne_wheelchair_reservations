from datetime import datetime

import streamlit as st

from common.constants import DeviceType
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_reservations

st.set_page_config(layout="wide")
st.header("Reservations")

# initialize data service
data_service = DataService()

# create tabs
all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
tabs = st.tabs([date.strftime("%a %b %d") for date in all_dates])

all_reservations = {
    date: data_service.get_reservations_on_date(date)
    for date in all_dates
}

for (date, reservations), tab in zip(all_reservations.items(), tabs):
    with tab:
        if reservations.empty:
            st.warning(f"**No Reservations Today**: There are no reservations for {date.strftime('%b %d, %Y')}.")
            continue
        st.subheader(f"{DeviceType.SCOOTER} Reservations")
        display_reservations(reservations, device_type=DeviceType.SCOOTER)
        st.subheader(f"{DeviceType.WHEELCHAIR} Reservations")
        display_reservations(reservations, device_type=DeviceType.WHEELCHAIR)
