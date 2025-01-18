from datetime import datetime, timedelta, time

import streamlit as st
from pydantic import ValidationError

from common.constants import DeviceType, Location
from common.data_models.reservation import NewReservation
from common.utils import get_default_timezone
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
        * **Date**: {new_reservation.date.strftime('%b %d, %Y')}
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
        ).astimezone(get_default_timezone())

        new_reservation = NewReservation(**new_reservation)
        status_code, result = data_service.add_new_reservation(reservation=new_reservation)
        if status_code == 200:
            display_success_dialog(reservation_id=result, new_reservation=new_reservation)

    except ValidationError as exc:
        display_validation_errors(exc.errors(), NewReservation)


initialize_reservation_form()
reservation_info = {}

col1, col2, col3 = st.columns(3)
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
reservation_info["location"] = col3.selectbox(
    label=NewReservation.model_fields["location"].title,
    options=Location,
    index=None,
    key="reservation_form_location",
)
if reservation_info["date"] and reservation_info["device_type"] and reservation_info["location"]:
    number_of_existing_reservations = data_service.get_number_of_reservations_on_date(
        date=reservation_info["date"],
        device_type=reservation_info["device_type"],
        location=reservation_info["location"],
    )
    match number_of_existing_reservations:
        case 0:
            quantifiers = "are", "s"
        case 1:
            quantifiers = "is", ""
        case _:
            quantifiers = "are", "s"
    st.info(
        f"**Note:** There {quantifiers[0]} {number_of_existing_reservations} existing "
        f"{reservation_info['device_type']} reservation{quantifiers[1]} on {reservation_info['date']} "
        f"at {reservation_info['location']}."
    )

    with st.form(key="reservation_form"):
        col1, col2, col3 = st.columns(3)
        reservation_info["name"] = col1.text_input(
            label=NewReservation.model_fields["name"].title,
            key="reservation_form_name",
        )
        reservation_info["phone_number"] = col2.text_input(
            label=NewReservation.model_fields["phone_number"].title,
            key="reservation_form_phone_number",
        )
        reservation_info["reservation_time"] = col3.time_input(
            label=NewReservation.model_fields["reservation_time"].title,
            step=timedelta(minutes=30),
            key="reservation_form_reservation_time",
        )

        reservation_info["notes"] = st.text_input(
            label=NewReservation.model_fields["notes"].title + " (optional)",
            key="reservation_form_notes",
        )
        submit = st.form_submit_button(label="Submit")

    if submit:
        submit_form(reservation_info)
