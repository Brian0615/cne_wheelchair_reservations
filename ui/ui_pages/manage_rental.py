import streamlit as st

from common.constants import Location
from common.data_models import ChangeDeviceInfo
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.rental_utils import change_rental_device
from ui.src.utils import display_validation_errors, get_rental_selection

initialize_page(page_header="Manage Rental")
data_service = DataService()

# retrieve a particular rental
date, rental_id, rental_data = get_rental_selection(
    data_service=data_service,
    in_progress_rentals_only=True,
    key_prefix="manage_rental",
)
if rental_id is None:
    st.stop()

with st.expander(f"Update Rental {rental_data['device_type'].value}", expanded=True):
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
        if not available_devices:
            st.warning("**No Available Devices**: There are no available devices at this location.")
            st.stop()
        change_device_info["new_device_id"] = col2.selectbox(
            label=f"New {rental_data['device_type'].value} ID",
            options=sorted(available_devices, key=lambda x: int(x[1:])),
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
            label=f"Update {rental_data['device_type'].value}",
            on_click=change_rental_device,
            args=(change_device_info,),
            disabled=not allow_submission,
            key="change_device_submit_button",
        )
