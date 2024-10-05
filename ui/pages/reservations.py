import datetime

import pandas as pd
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
all_dates = CNEDates.get_cne_date_list(year=datetime.datetime.today().year)
today_date = CNEDates.get_default_date()
all_dates = all_dates[all_dates.index(today_date):] + [" "] * 3 + all_dates[:all_dates.index(today_date)]
tabs = st.tabs([date.strftime("%a %b %d") if isinstance(date, datetime.date) else date for date in all_dates])

all_reservations = {
    date: data_service.get_reservations_on_date(date)
    for date in all_dates
    if isinstance(date, datetime.date)
}

for date, tab in zip(all_dates, tabs):
    if not isinstance(date, datetime.date):
        continue
    reservations = all_reservations.get(date, pd.DataFrame())

    with tab:
        if reservations.empty:
            st.warning(f"**No Reservations Today**: There are no reservations for {date.strftime('%b %d, %Y')}.")
            continue
        scooter_reservations, wheelchair_reservations = (
            reservations[reservations["device_type"] == DeviceType.SCOOTER],
            reservations[reservations["device_type"] == DeviceType.WHEELCHAIR],
        )
        st.subheader(f"{DeviceType.SCOOTER} Reservations")
        display_reservations(scooter_reservations, device_type=DeviceType.SCOOTER)
        st.subheader(f"{DeviceType.WHEELCHAIR} Reservations")
        display_reservations(wheelchair_reservations, device_type=DeviceType.WHEELCHAIR)
