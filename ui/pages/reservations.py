from datetime import datetime, timedelta, time

import pytz
import streamlit as st
from pydantic import ValidationError

from common.constants import DeviceType, Location
from common.data_models.reservation import NewReservation
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import load_reservations_for_date, display_validation_errors

st.set_page_config(layout="wide")
st.header("Reservations")

# initialize data service
data_service = DataService()

# create tabs
all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
tabs = st.tabs([date.strftime("%a %b %d") for date in all_dates])

all_reservations = {
    date.date(): load_reservations_for_date(date)
    for date in all_dates
}

for (_, reservations), tab in zip(all_reservations.items(), tabs):
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

st.divider()
with st.expander("Create a New Reservation"):
    st.info(
        """
        Use this form to create a new reservation. Click "Submit" to save the reservation.
        """
    )
    with st.form(key="new_reservation_form", clear_on_submit=True):

        col1, col2 = st.columns(2)
        reservation_date = col1.date_input(
            label=NewReservation.model_fields["date"].title,
            min_value=min(all_dates),
            max_value=max(all_dates),
        )
        reservation_type = col2.selectbox(
            label=NewReservation.model_fields["device_type"].title,
            options=DeviceType,
            index=None,
        )
        name = col1.text_input(label=NewReservation.model_fields["name"].title)
        phone_number = col2.text_input(NewReservation.model_fields["phone_number"].title)
        location = col1.selectbox(label=NewReservation.model_fields["location"].title, options=Location, index=None)
        time = col2.time_input(
            label=NewReservation.model_fields["pickup_time"].title + " (EST)",
            value=time(hour=10),
            step=timedelta(minutes=30),
        )
        notes = st.text_input(label=NewReservation.model_fields["notes"].title)

        submit = st.form_submit_button("Submit")

    if submit:
        try:
            new_reservation = NewReservation(
                date=reservation_date,
                device_type=reservation_type,
                name=name,
                phone_number=phone_number,
                location=location,
                pickup_time=datetime.combine(reservation_date, time).astimezone(pytz.timezone("America/Toronto")),
                notes=notes if notes else "N/A",
            )

            status_code, result = data_service.add_new_reservation(reservation=new_reservation)
            if status_code == 200:
                st.success(
                    f"Successfully added a **{reservation_type.lower()}** reservation for **{name}** "
                    f"on **{reservation_date.strftime('%b %d')}**. The reservation ID is: **{result}**")

        except ValidationError as exc:
            display_validation_errors(exc.errors(), NewReservation)
