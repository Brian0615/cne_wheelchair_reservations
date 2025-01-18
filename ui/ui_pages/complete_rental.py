from datetime import datetime

import numpy as np
import streamlit as st
from PIL import Image
from pydantic import ValidationError
from streamlit_drawable_canvas import st_canvas

from common.constants import Location
from common.data_models import CompletedRental
from common.utils import get_default_timezone
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_validation_errors, encode_signature_base64

initialize_page(page_header="Complete Rental")
data_service = DataService()


def clear_complete_rental_form():
    """Clear session state data with a given key prefix"""
    for key in st.session_state.keys():
        if key.startswith("complete_rental_"):
            if key.endswith("date"):
                st.session_state[key] = CNEDates.get_default_date()
            elif key.endswith("time"):
                st.session_state[key] = datetime.now().time()
            else:
                st.session_state[key] = None


@st.dialog("Success!")
def display_success_dialog(completed_rental: CompletedRental):
    st.success(
        f"""
        The following rental was completed successfully:

        * **Name**: {completed_rental.name}
        * **Returned Chair/Scooter**: {completed_rental.device_id}
        """
    )
    if st.button("Close"):
        clear_complete_rental_form()
        st.rerun()


def complete_rental(rental_completion_info: dict, signature: np.array):
    # clear previous errors
    st.session_state["complete_rental_errors"] = None
    try:
        # process signature
        signature = Image.fromarray(signature)
        rental_completion_info["return_signature"] = encode_signature_base64(signature)

        # update return time
        rental_completion_info["return_time"] = datetime.combine(
            date=rental_completion_info["date"],
            time=rental_completion_info["return_time"],
            tzinfo=get_default_timezone(),
        )
        rental_completion_info.pop("date")

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

    except ValidationError as exc:
        st.session_state["complete_rental_errors"] = exc.errors()


# retrieve a particular rental
col1, col2 = st.columns([1, 2])
all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
date = col1.date_input(
    label="Rental Date",
    value=CNEDates.get_default_date(),
    min_value=all_dates[0],
    max_value=all_dates[-1],
)
rentals = data_service.get_rentals_on_date(date=date, in_progress_rentals_only=True)
if rentals.empty:
    st.warning(f"**No Rentals**: There are no rentals on {date.strftime('%b %d, %Y')}.")
    st.stop()

rental_id = col2.selectbox(
    label="Select a Rental",
    options=sorted(rentals["device_id"] + " - " + rentals["name"] + " (Rental ID: " + rentals["id"] + ")"),
    index=None,
)
rental_id = rental_id.split("Rental ID: ")[1][:-1] if rental_id else None
if not rental_id:
    st.stop()
rental = rentals.loc[rentals["id"] == rental_id].to_dict(orient="records")[0]

# rental completion form
col1, col2, col3 = st.columns(3)
completed_rental_info = {
    "id": rental_id,
    "date": date,
    "name": rental["name"],
    "device_id": rental["device_id"],
    "return_time": col1.time_input(
        label="Return Time",
        value=datetime.now(get_default_timezone()).time(),
        key="complete_rental_time",
    ),
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
    f"**By checking the box(es) and signing below I, {rental['name']}, "
    f"confirm that the following have been returned to me:**"
)

check_items = True
if rental["items_left_behind"]:
    check_items = st.checkbox("Items Left Behind during Rental: " + ", ".join(rental["items_left_behind"]))
check_deposit = st.checkbox(f"{rental['deposit_payment_method']} Deposit of $50")
st.write("Signature")
canvas_signature = st_canvas(
    stroke_width=2,
    stroke_color="#1E90FF",
    height=100,
    key="complete_rental_signature",
)
canvas_signature = canvas_signature.image_data

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
)
