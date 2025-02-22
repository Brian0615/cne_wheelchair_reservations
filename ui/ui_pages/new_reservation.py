from datetime import datetime, time

import streamlit as st
from pydantic import ValidationError

from common.data_models.reservation import NewReservation
from common.utils import get_default_timezone
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.reservation_utils import render_reservation_form
from ui.src.utils import clear_session_state_for_form, display_validation_errors

initialize_page(page_header="New Reservation")
data_service = DataService()


def initialize_reservation_form():
    """Initialize the reservation form with default values"""
    if "reservation_form_date" not in st.session_state:
        st.session_state["reservation_form_date"] = CNEDates.get_default_new_reservation_date()
    if "reservation_form_reservation_time" not in st.session_state:
        st.session_state["reservation_form_reservation_time"] = time(hour=10)


@st.dialog("Success!")
def display_success_dialog(reservation_id: str, new_reservation: NewReservation):
    """Display the success dialog upon creating a new reservation"""
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
        clear_session_state_for_form(
            clear_prefixes=["reservation_form_"],
            default_date=CNEDates.get_default_new_reservation_date(),
            default_time=time(hour=10),
        )
        st.rerun()


def submit_form(new_reservation: dict):
    """Submit the reservation form"""
    # clear previous errors
    st.session_state["reservation_form_errors"] = None
    try:
        new_reservation["reservation_time"] = get_default_timezone().localize(
            datetime.combine(new_reservation["date"], new_reservation["reservation_time"])
        )

        new_reservation = NewReservation(**new_reservation)
        status_code, result = data_service.add_new_reservation(reservation=new_reservation)
        data_service.get_reservations_on_date.clear()
        if status_code == 200:
            display_success_dialog(reservation_id=result, new_reservation=new_reservation)

    except ValidationError as exc:
        display_validation_errors(exc.errors(), NewReservation)


initialize_reservation_form()
reservation_info, is_submitted = render_reservation_form(border=True)
if is_submitted:
    submit_form(new_reservation=reservation_info)
