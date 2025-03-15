from datetime import datetime
from typing import Union

import streamlit as st

from common.constants import ReservationStatus
from common.data_models.reservation import Reservation, NewReservation
from common.utils import get_default_timezone
from ui.forms.reservation_form import ReservationForm
from ui.src.data_service import DataService
from ui.src.utils import process_validation_errors


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
        st.rerun()


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
    status_code = DataService().update_reservation(reservation=reservation)
    if status_code == 200:
        display_success_dialog(reservation_id=reservation.id, reservation=reservation, is_update=True)
        ReservationForm(key_prefix="update_reservation").clear_form()


def update_reservation_status(reservation: Reservation, status: ReservationStatus):
    """Update the reservation status"""
    reservation.status = status
    status_code = DataService().update_reservation_status(reservation_id=reservation.id, status=status)
    if status_code == 200:
        display_success_dialog(reservation_id=reservation.id, reservation=reservation, is_update=True)
