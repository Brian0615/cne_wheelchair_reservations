import streamlit as st

from common.constants import ReservationStatus
from common.data_models import Reservation
from common.utils import get_default_timezone
from ui.forms import ReservationForm
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.reservation_utils import submit_update_reservation_form, update_reservation_status
from ui.src.utils import display_validation_errors, get_date_input

initialize_page(page_header="Manage Reservations")

# initialize data service
data_service = DataService()

# get date input and load reservations for that date
date_col, reservation_col = st.columns([1, 2])
reservation_date = get_date_input(label="Reservation Date", key_prefix="manage_reservations", col=date_col)
reservations = data_service.get_reservations_on_date(date=reservation_date)
if reservations is None or reservations.empty:
    st.warning(f"**No Reservations**: There are no reservations for {reservation_date.strftime('%b %d, %Y')}.")
    st.stop()

# get reservation ID
reservation_id = reservation_col.selectbox(
    label="Select a Reservation",
    options=sorted(
        reservations["id"] + " - " + reservations["name"]
        + " (" + reservations["reservation_time"].dt.tz_convert(get_default_timezone()).dt.strftime("%I:%M %p")
        + ", " + reservations["location"] + ")"
    ),
    index=None,
    on_change=ReservationForm(key_prefix="update_reservation").clear_form,
    key="manage_reservations_id_selection",
)
if not reservation_id:
    st.stop()
reservation_id = reservation_id.split("-")[0].strip()
reservation = Reservation(**reservations.loc[reservations["id"] == reservation_id].to_dict(orient="records")[0])
disable_edits = reservation.status in {
    ReservationStatus.PICKED_UP,
    ReservationStatus.COMPLETED,
    ReservationStatus.CANCELLED
}
if disable_edits:
    st.warning(
        "**Note**: You may not edit a reservation that has been picked up, completed, or cancelled. "
        "You may view the reservation details below."
    )

confirm_cancel_col, update_col = st.columns([1, 2])
with confirm_cancel_col.expander("Confirm or Cancel Reservation", expanded=True):
    match reservation.status:
        case ReservationStatus.CANCELLED:
            status_func = st.error
        case ReservationStatus.CONFIRMED:
            status_func = st.success
        case ReservationStatus.PENDING:
            status_func = st.warning
        case _:
            status_func = st.info
    status_func(f"Reservation Status: **{reservation.status}**")
    st.button(
        label="Confirm Reservation",
        use_container_width=True,
        icon=":material/check_circle:",
        disabled=disable_edits or reservation.status == ReservationStatus.CONFIRMED,
        key="confirm_reservation",
        on_click=update_reservation_status,
        kwargs={"reservation": reservation, "status": ReservationStatus.CONFIRMED},
    )
    st.button(
        "Cancel Reservation",
        use_container_width=True,
        icon=":material/cancel:",
        disabled=disable_edits,
        key="cancel_reservation",
        on_click=update_reservation_status,
        kwargs={"reservation": reservation, "status": ReservationStatus.CANCELLED},
    )

with update_col.expander("Change Reservation Info", expanded=True):
    st.info(
        "**Note**: The reservation date or device type may not be changed. "
        "If you wish to do so, cancel this reservation and create a new one."
    )
    reservation_form = ReservationForm(
        key_prefix="update_reservation",
        existing_reservation=reservation,
        disabled=disable_edits,
    )
    reservation_form.initialize_form()
    updated_reservation, is_submitted = reservation_form.render_form()
    updated_reservation["id"] = reservation.id
    updated_reservation["status"] = reservation.status
errors = st.session_state.get("update_reservation_form_errors")
if errors:
    display_validation_errors(errors, Reservation)
if is_submitted:
    submit_update_reservation_form(reservation=updated_reservation)
