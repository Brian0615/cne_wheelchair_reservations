from datetime import datetime

import streamlit as st

from common.constants import DeviceType, WALK_IN_RESERVATION_ID, RentalStatus
from common.data_models import CompletedRental, NewRental, ChangeDeviceInfo
from common.utils import get_default_timezone
from ui.forms import NewRentalForm
from ui.pdf_forms.scooter_pdf_form import ScooterPDFForm
from ui.pdf_forms.wheelchair_pdf_form import WheelchairPDFForm
from common.cne_dates import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import clear_session_state_for_form, process_validation_errors


def on_dismiss_complete_rental_success_dialog():
    """Callback for when the success dialog is dismissed"""
    clear_session_state_for_form(clear_prefixes=["complete_rental_"])


@st.dialog("Success!", on_dismiss=on_dismiss_complete_rental_success_dialog)
def display_complete_rental_success_dialog(completed_rental: CompletedRental):
    """Display the success dialog upon completing a rental"""

    st.success(
        f"""
        The following rental was completed successfully:

        * **Rental ID**: {completed_rental.id}
        * **Name**: {completed_rental.name}
        * **Returned Chair/Scooter**: {completed_rental.device_id}
        """
    )


def on_dismiss_new_rental_success_dialog():
    """Callback for when the success dialog is dismissed"""
    clear_session_state_for_form(clear_prefixes=["new_rental_"])
    NewRentalForm(key_prefix="new_rental").clear_form()


@st.dialog("Success!", on_dismiss=on_dismiss_new_rental_success_dialog)
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
    st.download_button(
        label="Download Rental Form",
        data=form_data,
        icon=":material/download:",
        file_name=f"rental_form_{rental_id}.pdf",
    )


def get_pdf_form_class(device_type: DeviceType):
    """Get the PDF form class based on the device type"""
    if device_type == DeviceType.WHEELCHAIR:
        return WheelchairPDFForm
    if device_type == DeviceType.SCOOTER:
        return ScooterPDFForm
    raise ValueError(f"Unsupported device type: {device_type}")


@process_validation_errors(error_key="complete_rental_errors")
def submit_complete_rental_form(completed_rental: dict):
    """Complete a rental"""

    completed_rental["cne_year"] = CNEDates.get_cne_year()

    # update return time
    completed_rental["return_time"] = get_default_timezone().localize(
        datetime.combine(completed_rental["return_date"], completed_rental["return_time"])
    )
    completed_rental.pop("return_date")

    # validate rental completion data
    completed_rental = CompletedRental(**completed_rental)

    # complete rental
    data_service = DataService()
    status_code, result = data_service.complete_rental(completed_rental)
    if status_code == 200:
        display_complete_rental_success_dialog(completed_rental)
    else:
        st.error(
            f"""
            **API Error**
            * Error Code: {status_code}
            * Error Message: {result}
            """
        )


@process_validation_errors(error_key="rental_form_errors")
def submit_new_rental_form(new_rental: dict):
    """Submit the new rental form"""

    new_rental["cne_year"] = CNEDates.get_cne_year()
    new_rental["pickup_time"] = get_default_timezone().localize(
        datetime.combine(new_rental["date"], new_rental["pickup_time"])
    )
    new_rental["status"] = RentalStatus.IN_PROGRESS

    # don't put reservation ID if walk-in
    if new_rental["reservation_id"] == WALK_IN_RESERVATION_ID:
        new_rental["reservation_id"] = None

    # validate rental data
    new_rental = NewRental(**new_rental)

    # try to add the new rental
    data_service = DataService()
    status_code, add_result = data_service.add_new_rental(new_rental)
    if status_code == 200:
        form_data = get_pdf_form_class(device_type=new_rental.device_type)(
            rental_data=new_rental,
            rental_id=add_result,
        ).export_form_to_bytes()
        status_code, upload_result = data_service.upload_rental_form(pdf_bytes=form_data, rental_id=add_result)

        if status_code == 200:
            display_new_rental_success_dialog(rental_id=add_result, new_rental=new_rental, form_data=form_data)
        else:
            st.error(
                f"""
                **API Error**
                * Error Code: {status_code}
                * Error Message: {upload_result}
                """
            )
    else:
        st.error(
            f"""
            **API Error**
            * Error Code: {status_code}
            * Error Message: {add_result}
            """
        )


def on_dismiss_change_device_success_dialog():
    """Callback for when the success dialog is dismissed"""
    clear_session_state_for_form(clear_prefixes=["manage_rental_", "change_device_"])


@st.dialog("Success!", on_dismiss=on_dismiss_change_device_success_dialog)
def display_change_device_success_dialog(change_data: ChangeDeviceInfo):
    """Display the success dialog upon changing a device"""
    st.success(
        f"""
        The following rental was updated successfully:

        * **Rental ID**: {change_data.id}
        * **Old Device ID**: {change_data.old_device_id}
        * **New Device ID**: {change_data.new_device_id}
        """
    )


@process_validation_errors(error_key="change_device_errors")
def change_rental_device(change_data: dict):
    """Change a device on a current rental"""

    # validate change device data
    change_data = ChangeDeviceInfo(**change_data)

    # change device
    status_code, _ = DataService().change_rental_device(change_data)
    if status_code == 200:
        display_change_device_success_dialog(change_data)
