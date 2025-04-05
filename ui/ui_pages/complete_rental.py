# pylint: disable=invalid-name
import numpy as np
import streamlit as st

from common.data_models import CompletedRental, RentalSummary
from ui.forms.complete_rental_form import CompleteRentalForm
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.rental_utils import submit_complete_rental_form
from ui.src.utils import display_validation_errors, get_rental_selection

initialize_page(page_header="Complete Rental")
data_service = DataService()

# retrieve a particular rental
date, rental_id, rental_data = get_rental_selection(
    data_service=data_service,
    in_progress_rentals_only=True,
    key_prefix="complete_rental",
)
if rental_id is None:
    st.stop()

form = CompleteRentalForm(key_prefix="complete_rental", rental_info=RentalSummary(**rental_data))
form.initialize_form()
completed_rental_info, is_submitted = form.render_form()
completed_rental_info["date"] = date
completed_rental_info["id"] = rental_id
completed_rental_info["name"] = rental_data["name"]
completed_rental_info["device_id"] = rental_data["device_id"]


# form submission or errors
errors = st.session_state.get("complete_rental_errors")
if errors:
    display_validation_errors(errors, CompletedRental)

if is_submitted:
    allow_submission = True
    if not completed_rental_info["check_items_deposit"]:
        st.error("Please confirm that the deposit and all items left behind (if any) have been returned.")
        allow_submission = False
    if not np.count_nonzero(np.max(completed_rental_info["return_signature"], axis=-1)) > 500:
        st.info(
            "**Signature Required**: Please sign in the box above to confirm that the above items have been returned."
        )
        allow_submission = False

    if allow_submission:
        completed_rental_info.pop("check_items_deposit")
        submit_complete_rental_form(completed_rental_info)
