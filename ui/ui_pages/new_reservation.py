from common.data_models.reservation import NewReservation
from ui.src.auth_utils import initialize_page
from ui.src.reservation_utils import render_reservation_form, submit_reservation_form


initialize_page(page_header="New Reservation")
reservation_info, is_submitted = render_reservation_form(border=True)
if is_submitted:
    submit_reservation_form(reservation=reservation_info, reservation_model=NewReservation)
