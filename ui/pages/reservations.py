from datetime import datetime

import streamlit as st

from ui.src.constants import CNEDates
from ui.src.utils import load_reservations_for_date

st.set_page_config(layout="wide")
st.header("Reservations")

# create tabs
all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
tabs = st.tabs([date.strftime("%a %b %d") for date in all_dates])

for date, tab in zip(all_dates, tabs):
    reservations = load_reservations_for_date(date)
    with tab:
        st.dataframe(
            data=reservations,
            column_config={
                "name": st.column_config.TextColumn(label="Name"),
                "phone_number": st.column_config.TextColumn(label="Phone Number"),
                "location": st.column_config.TextColumn(label="Location"),
                "reservation_time": st.column_config.TimeColumn(label="Reservation Time", format="HH a"),
                "notes": st.column_config.TextColumn(label="Notes", width="medium"),
                "is_picked_up": st.column_config.CheckboxColumn(label="Picked Up", width="small"),
                "time_out": st.column_config.TimeColumn(label="Time Out", format="hh:mm a", width="small"),
                "time_in": st.column_config.TimeColumn(label="Time In", format="hh:mm a", width="small"),
            },
            use_container_width=True,
        )
