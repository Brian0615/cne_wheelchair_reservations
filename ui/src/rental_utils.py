from datetime import datetime

import streamlit as st

from common.constants import DeviceType
from common.data_models import NewRental, ChangeDeviceInfo
from common.utils import get_default_timezone
from ui.forms import NewRentalForm
from ui.src.data_service import DataService
from ui.src.signature import Signature
from ui.src.utils import clear_session_state_for_form, process_validation_errors
from ui.src.wheelchair_form import WheelchairForm


@st.dialog("Success!")
def display_new_rental_success_dialog(rental_id: str, new_rental: NewRental, form_data: bytes):
    """Display the success dialog upon creating a new rental"""
    st.success(
        f"""
        The following rental was created successfully:
        
        * **Name**: {new_rental.name}
        * **{new_rental.device_type}**: {new_rental.device_id}
        * **Rental ID**: {rental_id}
        """
    )
    if new_rental.device_type == DeviceType.WHEELCHAIR:
        st.download_button(
            label="Download Rental Form",
            data=form_data,
            icon=":material/download:",
            file_name=f"rental_form_{rental_id}.pdf",
        )
    if st.button("Close"):
        clear_session_state_for_form(clear_prefixes=["rental_form_"])
        st.rerun()


@process_validation_errors(error_key="rental_form_errors")
def submit_new_rental_form(new_rental: dict):
    """Submit the new rental form"""

    # process signature
    new_rental["signature"] = Signature(signature_data=new_rental["signature"]).encode_as_base64()

    # update pickup time
    new_rental["pickup_time"] = datetime.combine(
        date=new_rental["date"],
        time=new_rental["pickup_time"],
        tzinfo=get_default_timezone(),
    )

    # validate rental data
    new_rental = NewRental(**new_rental)

    # try to add the new rental
    data_service = DataService()
    status_code, rental_id = data_service.add_new_rental(new_rental)
    if new_rental.device_type == DeviceType.WHEELCHAIR:
        form_data = WheelchairForm(rental_data=new_rental, rental_id=rental_id).export_form_to_bytes()
        status_code, _ = data_service.upload_rental_form(pdf_bytes=form_data, rental_id=rental_id)
    else:
        form_data = None
    if status_code == 200:
        display_new_rental_success_dialog(rental_id=rental_id, new_rental=new_rental, form_data=form_data)
        NewRentalForm(key_prefix="new_rental").clear_form()


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


@process_validation_errors(error_key="change_device_errors")
def change_rental_device(change_data: dict):
    """Change a device on a current rental"""

    # validate change device data
    change_data = ChangeDeviceInfo(**change_data)

    # change device
    status_code, _ = DataService().change_rental_device(change_data)
    if status_code == 200:
        display_change_device_success_dialog(change_data)
