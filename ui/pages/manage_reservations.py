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
col1, _, _, _ = st.columns(4)
date = col1.date_input(
    label="View Reservations for:",
    value=CNEDates.get_default_date(),
    min_value=all_dates[0],
    max_value=all_dates[-1],
)
reservations = data_service.get_reservations_on_date(date=date)

if reservations.empty:
    st.warning(f"**No Reservations Today**: There are no reservations for {date.strftime('%b %d, %Y')}.")
    st.stop()
st.subheader(f"{DeviceType.SCOOTER} Reservations")
display_reservations(reservations, device_type=DeviceType.SCOOTER)
st.subheader(f"{DeviceType.WHEELCHAIR} Reservations")
display_reservations(reservations, device_type=DeviceType.WHEELCHAIR)
