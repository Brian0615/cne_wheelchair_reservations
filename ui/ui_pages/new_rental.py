import numpy as np
import streamlit as st
from streamlit_drawable_canvas import st_canvas

from common.constants import DeviceType, HoldItem, Location, PaymentMethod, WALK_IN_RESERVATION_ID
from common.data_models.rental import NewRental
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.rental_utils import submit_form
from ui.src.utils import display_validation_errors

initialize_page(page_header="New Rental")
data_service = DataService()

rental_info = {}

# Intro Section of Rental Form
with st.container(border=True):
    # first row of intro section of form
    col1, col2, col3, col4 = st.columns(4)
    all_dates = CNEDates.get_cne_date_list()
    rental_info["date"] = col1.date_input(
        label="Rental Date",
        min_value=min(all_dates),
        max_value=max(all_dates),
        key="rental_form_date",
    )
    rental_info["pickup_time"] = col2.time_input(label="Pickup Time", value="now", key="rental_form_pickup_time")
    rental_info["pickup_location"] = col3.selectbox(
        label="Pickup Location",
        options=Location,
        index=None,
        key="rental_form_pickup_location",
    )
    rental_info["device_type"] = col4.selectbox(
        label="Rental Type",
        options=DeviceType,
        index=None,
        key="rental_form_device_type",
    )

    if not all(rental_info.get(x) for x in ["date", "pickup_time", "pickup_location", "device_type"]):
        st.stop()

    # check whether there are available devices
    available_devices = data_service.get_available_devices(
        device_type=rental_info["device_type"],
        location=rental_info["pickup_location"],
    )
    if not available_devices:
        st.error(
            f"**No Available {rental_info["device_type"]}s**: "
            f"There are no available {rental_info["device_type"]}s "
            f"at the {rental_info["pickup_location"]} location."
        )
        st.stop()

    # second row of intro section of form
    reservations_df = data_service.get_reservations_on_date(
        date=rental_info["date"],
        device_type=rental_info["device_type"],
        exclude_picked_up_reservations=True,
    )
    if reservations_df.empty:
        reservations_list = []
    else:
        reservations_list = reservations_df["name"] + " (" + reservations_df["id"] + ")"
    col1, col2, _, _ = st.columns(4)
    rental_info["reservation_id"] = col1.selectbox(
        label="Reservation Name/ID",
        options=sorted(reservations_list) + [WALK_IN_RESERVATION_ID],
        index=None,
        key="rental_form_reservation_id",
    )
    if rental_info["reservation_id"]:
        if rental_info["reservation_id"] != WALK_IN_RESERVATION_ID:
            rental_info["reservation_id"] = rental_info["reservation_id"].split("(")[1].replace(")", "")
        else:
            rental_info["reservation_id"] = None

    rental_info["device_id"] = col2.selectbox(
        "Assigned Chair/Scooter",
        options=sorted(available_devices),
        index=None,
        key="rental_form_device_id",
    )

# Renter Information Section of Form
with st.container(border=True):
    st.subheader("Renter Information")
    col1, col2 = st.columns([2, 1])
    rental_info["name"] = col1.text_input(label="Name", key="rental_form_name")
    rental_info["phone_number"] = col2.text_input(label="Phone Number", key="rental_form_phone_number")

    col1, col2 = st.columns([2, 1])
    rental_info['address'] = col1.text_input(label="Address", key="rental_form_address")
    rental_info['city'] = col2.text_input(label="City", key="rental_form_city")
    col1, col2, col3 = st.columns(3)
    rental_info['province'] = col1.text_input(label="Province", value="Ontario", key="rental_form_province")
    rental_info['postal_code'] = col2.text_input(label="Postal Code", key="rental_form_postal_code")
    rental_info['country'] = col3.text_input(label="Country", value="Canada", key="rental_form_country")

    id_verified = st.checkbox("ID Verified?")

# Payment Information Section of Form
with st.container(border=True):
    st.subheader("Payment Information")
    col1, col2 = st.columns(2)
    rental_info["fee_payment_amount"] = DeviceType.get_fee_amount(rental_info["device_type"])
    rental_info['fee_payment_method'] = col1.selectbox(
        label=f"Payment Type for **${rental_info['fee_payment_amount']}** Fee",
        options=PaymentMethod.get_accepted_fee_payment_methods(),
        index=None,
        key="rental_form_fee_payment_method",
    )
    rental_info["deposit_payment_amount"] = DeviceType.get_deposit_amount(rental_info["device_type"])
    rental_info['deposit_payment_method'] = col2.selectbox(
        label=f"Payment Type for **${rental_info['deposit_payment_amount']}** Deposit",
        options=PaymentMethod.get_accepted_deposit_payment_methods(),
        index=None,
        key="rental_form_deposit_payment_method",
    )

# Additional Information Section of Form
with st.container(border=True):
    st.subheader("Additional Information")
    col1, col2 = st.columns(2)
    rental_info['staff_name'] = col1.text_input("Staff Name")
    rental_info['items_left_behind'] = col2.multiselect(
        "Items Left Behind by Renter",
        options=HoldItem,
        key="rental_form_items_left_behind",
    )

# Terms and Conditions Section of Form
with st.container(border=True):
    st.subheader("Terms and Conditions")
    st.markdown("insert bunch of conditions here...")

    st.markdown("By signing below, I agree to the terms and conditions above.")
    # pylint: disable=invalid-name
    canvas_signature = st_canvas(
        stroke_width=2,
        stroke_color="#1E90FF",
        height=100,
        key="rental_form_signature",
    ).image_data

# quick validation of renter agreement
allow_submission = all([
    np.count_nonzero(np.max(canvas_signature, axis=-1)) > 500,
    id_verified,
])

errors = st.session_state.get("rental_form_errors")
if errors:
    display_validation_errors(errors, NewRental)
if not allow_submission:
    st.info(
        """
        Before submitting, please ensure that you have read and agreed to the relevant 
        terms and conditions and have signed in the box above.
        """
    )
submit = st.button(
    label="Submit",
    on_click=submit_form,
    args=(rental_info, canvas_signature),
    disabled=not allow_submission,
)
