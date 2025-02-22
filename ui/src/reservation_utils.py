from datetime import timedelta, time
from typing import Optional

import streamlit as st

from common.constants import DeviceType, Location
from common.data_models.reservation import Reservation, NewReservation
from ui.src.constants import CNEDates


def initialize_reservation_form(existing_reservation: Optional[Reservation] = None):
    """Initialize the reservation form with default values"""
    if st.session_state.get("reservation_form_date") is None:
        st.session_state["reservation_form_date"] = (
            CNEDates.get_default_new_reservation_date()
            if existing_reservation is None else existing_reservation.date
        )
    if st.session_state.get("reservation_form_reservation_time") is None:
        st.session_state["reservation_form_reservation_time"] = (
            time(hour=10) if existing_reservation is None else existing_reservation.reservation_time
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
    reservation_info = {}
    with st.container(border=border):
        col1, col2, col3 = st.columns(3)
        all_dates = CNEDates.get_cne_date_list()
        reservation_info["date"] = col1.date_input(
            label=NewReservation.model_fields["date"].title,
            min_value=min(all_dates),
            max_value=max(all_dates),
            key="reservation_form_date",
            disabled=disable_edits and existing_reservation is not None,
        )
        reservation_info["device_type"] = col2.selectbox(
            label=NewReservation.model_fields["device_type"].title,
            options=DeviceType,
            index=None,
            key="reservation_form_device_type",
            disabled=disable_edits and existing_reservation is not None,
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
            key="reservation_form_reservation_time",
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
