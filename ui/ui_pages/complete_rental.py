from datetime import datetime

import numpy as np
import streamlit as st
from streamlit_drawable_canvas import st_canvas

from common.constants import Location
from common.data_models import CompletedRental
from common.utils import get_default_timezone
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.signature import Signature
from ui.src.utils import (
    clear_session_state_for_form,
    display_validation_errors,
    get_rental_selection,
    initialize_form,
    process_validation_errors,
)

initialize_page(page_header="Complete Rental")
data_service = DataService()


@st.dialog("Success!")
def display_success_dialog(completed_rental: CompletedRental):
    """Display the success dialog upon completing a rental"""

    st.success(
        f"""
        The following rental was completed successfully:

        * **Rental ID**: {completed_rental.id}
        * **Name**: {completed_rental.name}
        * **Returned Chair/Scooter**: {completed_rental.device_id}
        """
    )
    if st.button("Close"):
        clear_session_state_for_form(clear_prefixes=["complete_rental_"])
        st.rerun()


@process_validation_errors(error_key="complete_rental_errors")
def complete_rental(rental_completion_info: dict, signature_data: np.array):
    """Complete a rental"""

    # process signature
    rental_completion_info["return_signature"] = Signature(signature_data=signature_data).encode_as_base64()

    # update return time
    rental_completion_info["return_time"] = get_default_timezone().localize(
        datetime.combine(date=rental_completion_info.pop("date"), time=rental_completion_info["return_time"])
    )

    # validate rental completion data
    completed_rental = CompletedRental(**rental_completion_info)

    # complete rental
    status_code, result = data_service.complete_rental(completed_rental)
    if status_code == 200:
        display_success_dialog(completed_rental)
    else:
        st.error(
            f"""
            **API Error**
            * Error Code: {status_code}
            * Error Message: {result}
            """
        )


# retrieve a particular rental
date, rental_id, rental_data = get_rental_selection(
    data_service=data_service,
    in_progress_rentals_only=True,
    key_prefix="complete_rental",
)
if rental_id is None:
    st.stop()

initialize_form(form_prefix="complete_rental", set_default_time=True)
with st.container(border=True):
    # rental completion form
    col1, col2, col3 = st.columns(3)
    completed_rental_info = {
        "id": rental_id,
        "date": date,
        "name": rental_data["name"],
        "device_id": rental_data["device_id"],
        "return_time": col1.time_input(label="Return Time", key="complete_rental_time"),
        "return_location": col2.selectbox(
            label="Return Location",
            options=Location,
            index=None,
            key="complete_rental_location",
        ),
        "return_staff_name": col3.text_input(
            label="Staff Name",
            key="complete_rental_staff_name",
        ),
    }

    st.write(
        f"**By checking the box(es) and signing below I, {rental_data['name']}, "
        f"confirm that the following have been returned to me:**"
    )

    check_items = True  # pylint: disable=invalid-name
    if rental_data["items_left_behind"]:
        check_items = st.checkbox("Items Left Behind during Rental: " + ", ".join(rental_data["items_left_behind"]))
    check_deposit = st.checkbox(f"{rental_data['deposit_payment_method']} Deposit of $50")
    st.write("Signature")
    # pylint: disable=invalid-name
    canvas_signature = st_canvas(
        stroke_width=2,
        stroke_color="#1E90FF",
        height=100,
        key="complete_rental_signature",
    ).image_data

    # form submission or errors
    errors = st.session_state.get("complete_rental_errors")
    if errors:
        display_validation_errors(errors, CompletedRental)
    allow_submission = all([
        np.count_nonzero(np.max(canvas_signature, axis=-1)) > 500,
        completed_rental_info["return_location"],
        completed_rental_info["return_time"],
        completed_rental_info["return_staff_name"],
        check_deposit,
        check_items,
    ])
st.button(
    label="Complete Rental",
    on_click=complete_rental,
    args=(completed_rental_info, canvas_signature),
    disabled=not allow_submission,
    key="complete_rental_submit"
)
