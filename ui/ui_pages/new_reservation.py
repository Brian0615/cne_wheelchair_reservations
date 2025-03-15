import streamlit as st

from common.data_models.reservation import NewReservation
from ui.forms import ReservationForm
from ui.src.auth_utils import initialize_page
from ui.src.reservation_utils import submit_new_reservation_form
from ui.src.utils import display_validation_errors

initialize_page(page_header="New Reservation")
reservation_form = ReservationForm(key_prefix="new_reservation")
with st.container(border=True):
    reservation_form.initialize_form()
reservation_info, is_submitted = reservation_form.render_form()
errors = st.session_state.get("new_reservation_form_errors")
if errors:
    display_validation_errors(errors, NewReservation)
if is_submitted:
    submit_new_reservation_form(reservation=reservation_info)
