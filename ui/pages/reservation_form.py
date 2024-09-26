from datetime import datetime, timedelta, time

import pytz
import streamlit as st
from pydantic import ValidationError

from common.constants import DeviceType, Location
from common.data_models.reservation import NewReservation
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_validation_errors

st.set_page_config(layout="wide")
data_service = DataService()


def clear_session_state_data():
    st.session_state["new_reservation_id"] = None
    st.session_state["reservation_form_data"] = None
    st.session_state["reservation_form_errors"] = None


st.header("Create a New Reservation")
new_reservation_id = st.session_state.get("new_reservation_id")
if new_reservation_id:
    cached_reservation_form_data = st.session_state.get("reservation_form_data", {})
    st.success(
        f"Successfully added a **{cached_reservation_form_data.device_type.lower()}** reservation for "
        f"**{cached_reservation_form_data.name}** on **{cached_reservation_form_data.date.strftime('%b %d')}**. "
        f"The reservation ID is: **{new_reservation_id}**"
    )
    clear_session_state_data()

with st.form(key="create_reservation_form", clear_on_submit=True):
    # load cached reservation form data
    cached_reservation_form_data = st.session_state.get("reservation_form_data", {})

    col1, col2 = st.columns(2)
    all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
    default_date = CNEDates.get_default_reservation_date()
    reservation_date = col1.date_input(
        label=NewReservation.model_fields["date"].title,
        min_value=min(all_dates),
        max_value=max(all_dates),
        value=cached_reservation_form_data.date if cached_reservation_form_data else default_date,
    )
    reservation_type = col2.selectbox(
        label=NewReservation.model_fields["device_type"].title,
        options=DeviceType,
        index=(
            list(DeviceType).index(cached_reservation_form_data.device_type)
            if cached_reservation_form_data and cached_reservation_form_data.device_type
            else None
        ),
    )
    name = col1.text_input(
        label=NewReservation.model_fields["name"].title,
        value=cached_reservation_form_data.name if cached_reservation_form_data else None,
    )
    phone_number = col2.text_input(
        label=NewReservation.model_fields["phone_number"].title,
        value=cached_reservation_form_data.phone_number if cached_reservation_form_data else None,
    )
    location = col1.selectbox(
        label=NewReservation.model_fields["location"].title,
        options=Location,
        index=(
            list(Location).index(cached_reservation_form_data.location)
            if cached_reservation_form_data and cached_reservation_form_data.location
            else None
        ),
    )
    time = col2.time_input(
        label=NewReservation.model_fields["pickup_time"].title + " (EST)",
        step=timedelta(minutes=30),
        value=cached_reservation_form_data.pickup_time if cached_reservation_form_data else time(hour=10),
    )
    notes = st.text_input(
        label=NewReservation.model_fields["notes"].title,
        value=(
            cached_reservation_form_data.notes
            if (
                    cached_reservation_form_data
                    and cached_reservation_form_data.notes
                    and cached_reservation_form_data.notes != "N/A"
            )
            else None
        ),
    )

    # display any errors from the last form submission
    errors = st.session_state.get("reservation_form_errors")
    if errors:
        display_validation_errors(errors, NewReservation)

    submit = st.form_submit_button("Submit")

if submit:
    # cache unvalidated reservation form data
    st.session_state["reservation_form_data"] = NewReservation.model_construct(
        date=reservation_date,
        device_type=reservation_type,
        name=name,
        phone_number=phone_number,
        location=location,
        pickup_time=datetime.combine(reservation_date, time).astimezone(pytz.timezone("America/Toronto")),
        notes=notes,
    )

    # validate data and create reservation if valid
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
            st.session_state["new_reservation_id"] = result
    except ValidationError as exc:
        st.session_state["reservation_form_errors"] = exc.errors()

    st.rerun()
