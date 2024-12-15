from datetime import datetime
from enum import StrEnum

import numpy as np
import pytz
import streamlit as st
from PIL import Image
from pydantic import ValidationError
from streamlit_drawable_canvas import st_canvas

from common.constants import Location
from common.data_models import ChangeDeviceInfo, CompletedRental
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_validation_errors, encode_signature_base64, get_date_input

initialize_page(page_header="Manage Rental")
data_service = DataService()


class ManageRentalOptions(StrEnum):
    """Options for managing a rental"""
    COMPLETE_RENTAL = "Complete Rental"
    CHANGE_WHEELCHAIR_OR_SCOOTER = "Change Wheelchair or Scooter"


def clear_manage_rental_form():
    """Clear session state data with a given key prefix"""
    for key in st.session_state.keys():
        if key.startswith("manage_rental_") or key.startswith("complete_rental_") or key.startswith("change_device_"):
            if key.endswith("date"):
                st.session_state[key] = CNEDates.get_default_date()
            elif key.endswith("time"):
                st.session_state[key] = datetime.now().time()
            else:
                st.session_state[key] = None


@st.dialog("Success!")
def display_complete_rental_success_dialog(completed_rental: CompletedRental):
    st.success(
        f"""
        The following rental was completed successfully:
        
        * **Name**: {completed_rental.name}
        * **Returned Chair/Scooter**: {completed_rental.device_id}
        """
    )
    if st.button("Close"):
        clear_manage_rental_form()
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
            tzinfo=pytz.timezone("America/Toronto"),
        )
        rental_completion_info.pop("date")

        # validate rental completion data
        completed_rental = CompletedRental(**rental_completion_info)

        # complete rental
        status_code, result = data_service.complete_rental(completed_rental)
        if status_code == 200:
            display_complete_rental_success_dialog(completed_rental)

    except ValidationError as exc:
        st.session_state["complete_rental_errors"] = exc.errors()


@st.dialog("Success!")
def display_change_device_success_dialog(change_device_info: ChangeDeviceInfo):
    st.success(
        f"""
        The following rental was updated successfully:
        
        * **Rental ID**: {change_device_info.rental_id}
        * **Old Device ID**: {change_device_info.old_device_id}
        * **New Device ID**: {change_device_info.new_device_id}
        """
    )
    if st.button("Close"):
        clear_manage_rental_form()
        st.rerun()


def change_rental_device(change_device_info: dict):
    # clear previous errors
    st.session_state["change_device_errors"] = None

    try:
        # validate change device data
        change_device_info = ChangeDeviceInfo(**change_device_info)

        # change device
        status_code, result = data_service.change_rental_device(change_device_info)
        if status_code == 200:
            display_change_device_success_dialog(change_device_info)

    except ValidationError as exc:
        st.session_state["change_device_errors"] = exc.errors()


completed_rental_info = {}

# retrieve a particular rental
col1, col2, _, _ = st.columns(4)
date = get_date_input(label="View Rentals for:")

rentals = data_service.get_rentals_on_date(date=date, in_progress_rentals_only=True)
if rentals.empty:
    st.warning(f"**No Rentals Today**: There are no rentals on {date.strftime('%b %d, %Y')}.")
    st.stop()
rental_id = col1.selectbox(
    label="Select a Rental",
    options=sorted(rentals["device_id"] + " - " + rentals["name"] + " (Rental ID: " + rentals["id"] + ")"),
    index=None,
)
rental_id = rental_id.split("Rental ID: ")[1][:-1] if rental_id else None
if not rental_id:
    st.stop()
rental = rentals.loc[rentals["id"] == rental_id].to_dict(orient="records")[0]
option = col2.selectbox(
    label="Choose an Option",
    options=ManageRentalOptions,
    index=None,
)
if not option:
    st.stop()

# completing rental
if ManageRentalOptions(option) == ManageRentalOptions.COMPLETE_RENTAL:
    st.subheader("Complete Rental")
    col1, col2, col3, _ = st.columns(4)
    completed_rental_info = {
        "id": rental_id,
        "date": date,
        "return_location": col1.selectbox(
            label="Return Location",
            options=Location,
            index=None,
            key="complete_rental_location",
        ),
        "return_time": col2.time_input(
            label="Return Time",
            value=datetime.now().time(),
            key="complete_rental_time",
        ),
        "return_staff_name": col3.text_input(
            label="Staff Name",
            key="complete_rental_staff_name",
        ),
    }

    st.write(
        f"**By checking the box(es) and signing below I, {rental['name']}, confirm that the following have been returned to me:**")

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

if ManageRentalOptions(option) == ManageRentalOptions.CHANGE_WHEELCHAIR_OR_SCOOTER:
    st.subheader(f"Change {rental['device_type'].value}")
    change_device_info = {
        "rental_id": rental_id,
        "device_type": rental["device_type"],
        "old_device_id": rental["device_id"],
    }

    col1, col2, col3, _ = st.columns(4)
    change_device_info["location"] = col1.selectbox(
        label="Current Location",
        options=Location,
        index=None,
        key="change_device_location",
    )
    if change_device_info["location"] is not None:
        available_devices = data_service.get_available_devices(
            device_type=rental["device_type"],
            location=Location(change_device_info["location"]),
        )
        change_device_info["new_device_id"] = col2.selectbox(
            label=f"New {rental['device_type'].value} ID",
            options=available_devices,
            index=None,
            key="change_device_new_device_id",
        )
        change_device_info["staff_name"] = col3.text_input(label="Staff Name", key="change_device_staff_name")

        errors = st.session_state.get("change_device_errors")
        if errors:
            display_validation_errors(errors, ChangeDeviceInfo)

        allow_submission = all(
            [
                change_device_info.get("location"),
                change_device_info.get("new_device_id"),
                change_device_info.get("staff_name"),
            ]
        )
        st.button(
            label=f"Change {rental['device_type'].value}",
            on_click=change_rental_device,
            args=(change_device_info,),
            disabled=not allow_submission,
        )
