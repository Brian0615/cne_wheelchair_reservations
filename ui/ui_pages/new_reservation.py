from datetime import datetime, timedelta, time

import pytz
import streamlit as st
from pydantic import ValidationError

from common.constants import DeviceType, Location
from common.data_models.reservation import NewReservation
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_validation_errors

initialize_page(page_header="New Reservation")
data_service = DataService()


def initialize_reservation_form():
    if "reservation_form_date" not in st.session_state:
        st.session_state["reservation_form_date"] = CNEDates.get_default_new_reservation_date()
    if "reservation_form_reservation_time" not in st.session_state:
        st.session_state["reservation_form_reservation_time"] = time(hour=10)


def clear_reservation_form():
    for key in st.session_state.keys():
        if key.startswith("reservation_form_"):
            if key.endswith("date"):
                st.session_state[key] = CNEDates.get_default_new_reservation_date()
            elif key.endswith("reservation_time"):
                st.session_state[key] = time(hour=10)
            else:
                st.session_state[key] = None


@st.dialog("Success!")
def display_success_dialog(reservation_id: str, new_reservation: NewReservation):
    st.success(
        f"""
        The following **{new_reservation.device_type}** reservation was created successfully:
        
        * **Name**: {new_reservation.name}
        * **Date**: {new_reservation.date.strftime('%b %d')}
        * **Time**: {new_reservation.reservation_time.strftime('%I:%M %p')}
        * **Location**: {new_reservation.location}
        * **Reservation ID**: {reservation_id}
        """
    )
    if st.button("Close"):
        clear_reservation_form()  # clear the reservation form for the next reservation
        st.rerun()


def submit_form(new_reservation: dict):
    # clear previous errors
    st.session_state["reservation_form_errors"] = None
    try:
        new_reservation['reservation_time'] = datetime.combine(
            new_reservation['date'],
            new_reservation['reservation_time']
        ).astimezone(pytz.timezone("America/Toronto"))

        new_reservation = NewReservation(**new_reservation)
        status_code, result = data_service.add_new_reservation(reservation=new_reservation)
        if status_code == 200:
            display_success_dialog(reservation_id=result, new_reservation=new_reservation)

    except ValidationError as exc:
        st.session_state["reservation_form_errors"] = exc.errors()


initialize_reservation_form()
reservation_info = {}

# first row of form
col1, col2 = st.columns(2)
all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
reservation_info["date"] = col1.date_input(
    label=NewReservation.model_fields["date"].title,
    min_value=min(all_dates),
    max_value=max(all_dates),
    key="reservation_form_date",
)
reservation_info["device_type"] = col2.selectbox(
    label=NewReservation.model_fields["device_type"].title,
    options=DeviceType,
    index=None,
    key="reservation_form_device_type",
)

# second row of form
col1, col2 = st.columns(2)
reservation_info["name"] = col1.text_input(
    label=NewReservation.model_fields["name"].title,
    key="reservation_form_name",
)
reservation_info["phone_number"] = col2.text_input(
    label=NewReservation.model_fields["phone_number"].title,
    key="reservation_form_phone_number",
)

# third row of form
col1, col2 = st.columns(2)
reservation_info["location"] = col1.selectbox(
    label=NewReservation.model_fields["location"].title,
    options=Location,
    index=None,
    key="reservation_form_location",
)
reservation_info["reservation_time"] = col2.time_input(
    label=NewReservation.model_fields["reservation_time"].title,
    step=timedelta(minutes=30),
    key="reservation_form_reservation_time",
)

# fourth row of form
reservation_info["notes"] = st.text_input(
    label=NewReservation.model_fields["notes"].title + " (optional)",
    key="reservation_form_notes",
)

# display any errors from the last form submission
errors = st.session_state.get("reservation_form_errors")
if errors:
    display_validation_errors(errors, NewReservation)

submit = st.button(
    label="Submit",
    on_click=submit_form,
    args=(reservation_info,)
)
