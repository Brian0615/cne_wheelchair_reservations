from datetime import datetime, timedelta, time

import pytz
import streamlit as st
from pydantic import ValidationError

from common.constants import DeviceType, Location
from common.data_models.reservation import NewReservation
from src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_validation_errors

st.set_page_config(layout="wide")
data_service = DataService()


def reset_reservation_form():
    st.session_state["reservation_form_date"] = CNEDates.get_default_new_reservation_date()
    st.session_state["reservation_form_device_type"] = None
    st.session_state["reservation_form_name"] = None
    st.session_state["reservation_form_phone_number"] = None
    st.session_state["reservation_form_location"] = None
    st.session_state["reservation_form_pickup_time"] = time(hour=10)
    st.session_state["reservation_form_notes"] = None


def clear_successful_reservation_data():
    st.session_state["successful_reservation_id"] = None
    st.session_state["successful_reservation_form_data"] = None


def submit_form(new_reservation: NewReservation):
    # clear previous errors
    st.session_state["reservation_form_errors"] = None
    try:
        new_reservation = NewReservation(**new_reservation.model_dump())
        status_code, result = data_service.add_new_reservation(reservation=new_reservation)
        if status_code == 200:
            # save new session state
            st.session_state["successful_reservation_id"] = result
            st.session_state["successful_reservation_form_data"] = new_reservation
            reset_reservation_form()
    except ValidationError as exc:
        st.session_state["reservation_form_errors"] = exc.errors()


st.header("Create a New Reservation")

# first row of form
col1, col2 = st.columns(2)
all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
reservation_date = col1.date_input(
    label=NewReservation.model_fields["date"].title,
    min_value=min(all_dates),
    max_value=max(all_dates),
    key="reservation_form_date",
)
reservation_type = col2.selectbox(
    label=NewReservation.model_fields["device_type"].title,
    options=DeviceType,
    index=None,
    key="reservation_form_device_type",
)

# second row of form
col1, col2 = st.columns(2)
name = col1.text_input(
    label=NewReservation.model_fields["name"].title,
    key="reservation_form_name",
)
phone_number = col2.text_input(
    label=NewReservation.model_fields["phone_number"].title,
    key="reservation_form_phone_number",
)

# third row of form
col1, col2 = st.columns(2)
location = col1.selectbox(
    label=NewReservation.model_fields["location"].title,
    options=Location,
    index=None,
    key="reservation_form_location",
)
pickup_time = col2.time_input(
    label=NewReservation.model_fields["pickup_time"].title + " (EST)",
    step=timedelta(minutes=30),
    value=time(hour=10),
    key="reservation_form_pickup_time",
)

# fourth row of form
notes = st.text_input(
    label=NewReservation.model_fields["notes"].title,
    key="reservation_form_notes",
)

# display any errors from the last form submission
errors = st.session_state.get("reservation_form_errors")
if errors:
    display_validation_errors(errors, NewReservation)

submit = st.button(
    label="Submit",
    on_click=submit_form,
    args=(
        NewReservation.model_construct(
            date=reservation_date,
            device_type=reservation_type,
            name=name,
            phone_number=phone_number,
            location=location,
            pickup_time=datetime.combine(reservation_date, pickup_time).astimezone(pytz.timezone("America/Toronto")),
            notes=notes if notes else "N/A",
        ),
    )
)

# display success information if successful
new_reservation_id = st.session_state.get("successful_reservation_id")
if new_reservation_id:
    cached_reservation_form_data = st.session_state.get("successful_reservation_form_data", {})
    st.success(
        f"Successfully added a **{cached_reservation_form_data.device_type.lower()}** reservation for "
        f"**{cached_reservation_form_data.name}** on **{cached_reservation_form_data.date.strftime('%b %d')}**. "
        f"The reservation ID is: **{new_reservation_id}**"
    )
    clear_successful_reservation_data()
