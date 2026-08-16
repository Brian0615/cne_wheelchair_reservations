# pylint: disable=invalid-name
import streamlit as st

from common.data_models.rental import NewRental
from ui.forms import NewRentalForm
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.rental_utils import submit_new_rental_form
from ui.src.utils import display_validation_errors

initialize_page(page_header="New Rental")
data_service = DataService()

rental_form = NewRentalForm(key_prefix="new_rental")
rental_form.initialize_form()
rental_info, is_submitted = rental_form.render_form()

# fetch data for form field options
fields_refreshed = False
if rental_info.get("date") and rental_info.get("device_type"):
    reservations_df = data_service.get_reservations_on_date(
        date=rental_info["date"],
        device_type=rental_info["device_type"],
        exclude_picked_up_reservations=True,
    )
    if not reservations_df.empty:
        reservations_df = reservations_df.sort_values(by="id")
        reservations_list = (reservations_df["name"] + " (" + reservations_df["id"] + ")").tolist()
        if reservations_list != st.session_state.get("new_rental_reservations"):
            st.session_state["new_rental_reservations"] = reservations_list
            fields_refreshed = True
if rental_info.get("pickup_location") and rental_info.get("device_type"):
    available_devices = data_service.get_available_device_ids(device_type=rental_info["device_type"])
    if available_devices != st.session_state.get("new_rental_available_devices"):
        st.session_state["new_rental_available_devices"] = available_devices
        fields_refreshed = True
    if not available_devices:
        st.warning(
            f"**No Available {rental_info['device_type']}s**: "
            f"There are no available {rental_info['device_type']}s "
            f"at the {rental_info['pickup_location']} location."
        )
if rental_info.get("device_type"):
    fee_payment_amount = data_service.get_fee_amount(device_type=rental_info["device_type"])
    deposit_payment_amount = data_service.get_deposit_amount(device_type=rental_info["device_type"])
    if fee_payment_amount != st.session_state.get("new_rental_fee_payment_amount"):
        st.session_state["new_rental_fee_payment_amount"] = fee_payment_amount
        fields_refreshed = True
    if deposit_payment_amount != st.session_state.get("new_rental_deposit_payment_amount"):
        st.session_state["new_rental_deposit_payment_amount"] = deposit_payment_amount
        fields_refreshed = True

if fields_refreshed:
    st.rerun()

errors = st.session_state.get("rental_form_errors")
if errors:
    display_validation_errors(errors, NewRental)

if is_submitted:
    allow_submission = True
    if not rental_info["id_verified"]:
        st.error("**ID Not Verified**: Please confirm that the renter's ID has been verified.")
        allow_submission = False

    if allow_submission:
        rental_info.pop("id_verified")
        submit_new_rental_form(rental_info)
