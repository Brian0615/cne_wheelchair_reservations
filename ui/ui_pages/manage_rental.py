from enum import StrEnum

import streamlit as st
from pydantic import ValidationError

from common.constants import Location
from common.data_models import ChangeDeviceInfo
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.utils import clear_session_state_for_form, display_validation_errors, get_rental_selection

initialize_page(page_header="Manage Rental")
data_service = DataService()


class ManageRentalOptions(StrEnum):
    """Options for managing a rental"""
    COMPLETE_RENTAL = "Complete Rental"
    CHANGE_WHEELCHAIR_OR_SCOOTER = "Change Wheelchair or Scooter"


@st.dialog("Success!")
def display_change_device_success_dialog(change_data: ChangeDeviceInfo):
    """Display the success dialog upon changing a device"""
    st.success(
        f"""
        The following rental was updated successfully:
        
        * **Rental ID**: {change_data.rental_id}
        * **Old Device ID**: {change_data.old_device_id}
        * **New Device ID**: {change_data.new_device_id}
        """
    )
    if st.button("Close"):
        clear_session_state_for_form(clear_prefixes=["manage_rental_", "change_device_"])
        st.rerun()


def change_rental_device(change_data: dict):
    """Change a device on a current rental"""
    # clear previous errors
    st.session_state["change_device_errors"] = None

    try:
        # validate change device data
        change_data = ChangeDeviceInfo(**change_data)

        # change device
        status_code, _ = data_service.change_rental_device(change_data)
        if status_code == 200:
            display_change_device_success_dialog(change_data)

    except ValidationError as exc:
        st.session_state["change_device_errors"] = exc.errors()


completed_rental_info = {}

# retrieve a particular rental
date, rental_id, rental_data = get_rental_selection(data_service=data_service, in_progress_rentals_only=True)

st.subheader(f"Change {rental_data['device_type'].value}")
change_device_info = {
    "rental_id": rental_id,
    "device_type": rental_data["device_type"],
    "old_device_id": rental_data["device_id"],
}

col1, col2, col3 = st.columns(3)
change_device_info["location"] = col1.selectbox(
    label="Current Location",
    options=Location,
    index=None,
    key="change_device_location",
)
if change_device_info["location"] is not None:
    available_devices = data_service.get_available_devices(
        device_type=rental_data["device_type"],
        location=Location(change_device_info["location"]),
    )
    change_device_info["new_device_id"] = col2.selectbox(
        label=f"New {rental_data['device_type'].value} ID",
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
        label=f"Change {rental_data['device_type'].value}",
        on_click=change_rental_device,
        args=(change_device_info,),
        disabled=not allow_submission,
    )
