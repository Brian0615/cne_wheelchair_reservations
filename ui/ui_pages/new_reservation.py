# pylint: disable=invalid-name
import streamlit as st

from common.constants import DeviceType
from common.data_models.reservation import NewReservation
from ui.forms import ReservationForm
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.reservation_utils import submit_new_reservation_form, get_reservation_counts, \
    create_reservation_availability_chart
from ui.src.utils import display_validation_errors

initialize_page(page_header="New Reservation")
data_service = DataService()

# display the reservation limit for each device type
with st.expander("View Reservation Availability", expanded=False):
    reservation_counts = get_reservation_counts()
    cols = st.columns(len(DeviceType), gap="large")
    for col, device_type in zip(cols, DeviceType):
        limit = data_service.get_setting(setting_id=f"{device_type.lower()}_reservation_limit")
        with col:
            st.write("**" + device_type.title() + " Availability**")
            create_reservation_availability_chart(
                reservation_counts=reservation_counts,
                device_type=device_type,
                limit=int(limit) if limit is not None else 0,
                plot_height=200,
            )

# display the reservation form
reservation_form = ReservationForm(key_prefix="new_reservation")
with st.container(border=True):
    reservation_form.initialize_form()
    reservation_info, is_submitted = reservation_form.render_form()
errors = st.session_state.get("new_reservation_form_errors")
if errors:
    display_validation_errors(errors, NewReservation)

# Show warning if there are no more available reservations for the selected date/device/location
is_waitlisted = False
if reservation_info and reservation_info.get("date") and reservation_info.get("device_type"):

    # Get reservation limit for the selected device type
    device_str = reservation_info["device_type"].lower()
    reservation_limit = data_service.get_setting(setting_id=f"{device_str}_reservation_limit")

    if reservation_limit is not None:
        reservation_counts = data_service.get_reservation_count()
        num_existing = reservation_counts[
            (reservation_counts["date"].dt.date == reservation_info["date"])
            & (reservation_counts["device_type"] == reservation_info["device_type"])
            ]["count"].sum() if not reservation_counts.empty else 0
        num_available = int(reservation_limit) - num_existing
        if num_available <= 0:
            st.warning(f"""
                **No Available Reservations**: There are no more available {device_str} reservations for the
                selected date
                
                * Please try another date, or increase the reservation limit to allow more reservations
                * Alternatively, you can add a reservation onto the waitlist by submitting
                """
                       )
            is_waitlisted = True
        else:
            st.info(f"""
                **Reservations Available**: There {'are' if num_available > 1 else 'is'} **{num_available}** remaining
                {device_str} reservation{'s' if num_available > 1 else ''} available for the selected date
            """)

if is_submitted:
    submit_new_reservation_form(reservation=reservation_info, is_waitlisted=is_waitlisted)
