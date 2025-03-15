from datetime import datetime, timedelta, time
from typing import Optional, Union

import streamlit as st

from common.constants import DeviceType, Location, ReservationStatus
from common.data_models.reservation import Reservation, NewReservation
from common.utils import get_default_timezone
from ui.forms.reservation_form import ReservationForm
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import clear_session_state_for_form, initialize_form, \
    process_validation_errors


# pylint: disable=trailing-whitespace
@st.dialog("Success!")
def display_success_dialog(reservation_id: str, reservation: Union[NewReservation, Reservation], is_update: bool):
    """Display the success dialog upon creating/updating a reservation"""
    st.success(
        f"""
        The following **{reservation.device_type}** reservation was 
        {'updated' if is_update else 'created'} successfully:

        * **Reservation ID**: {reservation_id}
        * **Name**: {reservation.name}
        * **Date**: {reservation.date.strftime('%b %d, %Y')}
        * **Time**: {reservation.reservation_time.strftime('%I:%M %p')}
        * **Location**: {reservation.location}
        * **Status**: {reservation.status}
        """
    )
    if st.button("Close"):
        clear_session_state_for_form(clear_prefixes=["reservation_form_"])
        st.rerun()


def initialize_reservation_form(existing_reservation: Optional[Reservation] = None):
    """Initialize the reservation form with default values"""
    initialize_form(
        form_prefix="reservation_form",
        set_default_date=True,
        set_default_time=True,
        default_date=existing_reservation.date if existing_reservation else CNEDates.get_default_new_reservation_date(),
        default_time=existing_reservation.reservation_time if existing_reservation else time(hour=10)
    )

    for field in ["device_type", "location", "name", "phone_number", "notes"]:
        if st.session_state.get(f"reservation_form_{field}") is None and existing_reservation is not None:
            st.session_state[f"reservation_form_{field}"] = getattr(existing_reservation, field)


def render_reservation_form(
        existing_reservation: Optional[Reservation] = None,
        border: bool = False,
        disable_edits: bool = False,
):
    """
    Render the reservation form.

    Args:
        existing_reservation (Optional[Reservation]): Existing reservation data to pre-fill the form.
        border (bool): Whether to display a border around the form.
        disable_edits (bool): Whether to disable edits on the form. Ignored if `existing_reservation` is None.

    Returns:

    """
    initialize_reservation_form(existing_reservation=existing_reservation)
    reservation_info = {} if existing_reservation is None else existing_reservation.model_dump()
    with st.container(border=border):
        col1, col2, col3 = st.columns(3)
        all_dates = CNEDates.get_cne_date_list()
        reservation_info["date"] = col1.date_input(
            label=NewReservation.model_fields["date"].title,
            min_value=min(all_dates),
            max_value=max(all_dates),
            key="reservation_form_date",
            disabled=disable_edits or existing_reservation is not None,  # disallow date change for existing reservation
        )
        reservation_info["device_type"] = col2.selectbox(
            label=NewReservation.model_fields["device_type"].title,
            options=DeviceType,
            index=None,
            key="reservation_form_device_type",
            disabled=disable_edits or existing_reservation is not None,  # disallow type change for existing reservation
        )
        reservation_info["location"] = col3.selectbox(
            label=NewReservation.model_fields["location"].title,
            options=Location,
            index=None,
            key="reservation_form_location",
            disabled=disable_edits and existing_reservation is not None,
        )
        col1, col2, col3 = st.columns(3)
        reservation_info["name"] = col1.text_input(
            label=NewReservation.model_fields["name"].title,
            key="reservation_form_name",
            disabled=disable_edits and existing_reservation is not None,
        )
        reservation_info["phone_number"] = col2.text_input(
            label=NewReservation.model_fields["phone_number"].title,
            key="reservation_form_phone_number",
            disabled=disable_edits and existing_reservation is not None,
        )
        reservation_info["reservation_time"] = col3.time_input(
            label=NewReservation.model_fields["reservation_time"].title,
            step=timedelta(minutes=30),
            key="reservation_form_time",
            disabled=disable_edits and existing_reservation is not None,
        )
        reservation_info["notes"] = st.text_input(
            label=NewReservation.model_fields["notes"].title,
            key="reservation_form_notes",
            disabled=disable_edits and existing_reservation is not None,
        )
        st.divider()
        is_submitted = st.button(
            label="Submit Reservation" if existing_reservation is None else "Update Reservation",
            key="reservation_form_submit_button",
            disabled=disable_edits and existing_reservation is not None,
        )
    return reservation_info, is_submitted


@process_validation_errors(error_key="new_reservation_form_errors")
def submit_new_reservation_form(reservation: dict):
    """Submit the reservation form"""

    reservation["reservation_time"] = get_default_timezone().localize(
        datetime.combine(reservation["date"], reservation["reservation_time"])
    )

    reservation = NewReservation(**reservation)
    status_code, result = DataService().add_new_reservation(reservation=reservation)
    if status_code == 200:
        display_success_dialog(reservation_id=result, reservation=reservation, is_update=False)
        ReservationForm(key_prefix="new_reservation").clear_form()


@process_validation_errors(error_key="update_reservation_form_errors")
def submit_update_reservation_form(reservation: dict):
    """Submit the reservation form"""

    reservation["reservation_time"] = get_default_timezone().localize(
        datetime.combine(reservation["date"], reservation["reservation_time"])
    )

    reservation = Reservation(**reservation)
    status_code, result = DataService().update_reservation(reservation=reservation)
    if status_code == 200:
        display_success_dialog(reservation_id=result, reservation=reservation, is_update=False)
        ReservationForm(key_prefix="update_reservation").clear_form()


def update_reservation_status(reservation: Reservation, status: ReservationStatus):
    """Update the reservation status"""
    reservation.status = status
    status_code = DataService().update_reservation_status(reservation_id=reservation.id, status=status)
    if status_code == 200:
        display_success_dialog(reservation_id=reservation.id, reservation=reservation, is_update=True)
        clear_session_state_for_form(clear_prefixes=["reservation_form_"])
