import io
from datetime import datetime

import numpy as np
import pytz
import streamlit as st
from PIL import Image
from pydantic import ValidationError
from streamlit_drawable_canvas import st_canvas

from common.constants import DeviceType, ItemLeftBehind, Location, PaymentMethod, WALK_IN_RESERVATION_ID
from common.data_models.rental import NewRental
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_validation_errors

st.set_page_config(layout="wide")
data_service = DataService()


def submit_form(new_rental: NewRental, signature: np.array):
    # clear previous errors
    st.session_state["rental_form_errors"] = None
    try:
        # process signature
        signature = Image.fromarray(signature)
        signature_bytes = io.BytesIO()
        signature.save(signature_bytes, format="PNG")
        new_rental.signature = signature_bytes.getvalue()

        # validate rental data
        _ = NewRental(**new_rental.model_dump())
    except ValidationError as exc:
        st.session_state["rental_form_errors"] = exc.errors()


st.header("Rental Form")
rental_information = {}

# first row of intro section of form
col1, col2, col3, col4 = st.columns(4)
rental_information["date"] = col1.date_input(label="Rental Date", value=CNEDates.get_default_date())
rental_information["pickup_time"] = datetime.combine(
    rental_information["date"],
    col2.time_input(label="Pickup Time", value="now"),
    tzinfo=pytz.timezone("America/Toronto"),
)
rental_information["pickup_location"] = col3.selectbox("Pickup Location", options=Location, index=None)
rental_information["device_type"] = col4.selectbox("Rental Type", options=DeviceType, index=None)

if not all(rental_information.get(x) for x in ["date", "pickup_time", "pickup_location", "device_type"]):
    st.stop()

# second row of intro section of form
available_devices = data_service.get_available_devices(
    device_type=rental_information["device_type"],
    location=rental_information["pickup_location"],
)
if not available_devices:
    st.error(
        f"**No Available {rental_information["device_type"]}s**: "
        f"There are no available {rental_information["device_type"]}s "
        f"at the {rental_information["pickup_location"]} location."
    )
    st.stop()
reservations_df = data_service.get_reservations_on_date(
    date=rental_information["date"],
    device_type=rental_information["device_type"],
)
reservations_list = reservations_df["name"] + " (" + reservations_df["id"] + ")"
col1, col2, _, _ = st.columns(4)
rental_information["reservation_id"] = col1.selectbox(
    label="Reservation Name/ID",
    options=sorted(reservations_list) + [WALK_IN_RESERVATION_ID],
    index=None,
)
if rental_information["reservation_id"] and rental_information["reservation_id"] != WALK_IN_RESERVATION_ID:
    rental_information["reservation_id"] = rental_information["reservation_id"].split("(")[1].replace(")", "")

rental_information["device_id"] = col2.selectbox(
    "Assigned Chair/Scooter",
    options=available_devices,
    index=None,
    help="Select the assigned wheelchair or scooter. \n\n"
         "**Note**: This field is only available once the rental type and location are selected."
)

st.divider()

st.subheader("Renter Information")

col1, col2 = st.columns([2, 1])
rental_information["name"] = col1.text_input(label="Name")
rental_information["phone_number"] = col2.text_input(label="Phone Number")

col1, col2 = st.columns([2, 1])
rental_information['address'] = col1.text_input(label="Address")
rental_information['city'] = col2.text_input(label="City")
col1, col2, col3 = st.columns(3)
rental_information['province'] = col1.text_input(label="Province")
rental_information['postal_code'] = col2.text_input(label="Postal Code")
rental_information['country'] = col3.text_input(label="Country", value="Canada")

id_verified = st.checkbox("ID Verified?")

st.divider()
st.subheader("Payment Information")
col1, col2 = st.columns(2)
rental_information["fee_payment_amount"] = DeviceType.get_fee_amount(rental_information["device_type"])
rental_information['fee_payment_method'] = col1.selectbox(
    label=f"Payment Type for **${rental_information['fee_payment_amount']}** Fee",
    options=PaymentMethod.get_accepted_fee_payment_methods(),
    index=None,
)
rental_information["deposit_payment_amount"] = DeviceType.get_deposit_amount(rental_information["device_type"])
rental_information['deposit_payment_method'] = col2.selectbox(
    label=f"Payment Type for **${rental_information['deposit_payment_amount']}** Deposit",
    options=PaymentMethod.get_accepted_deposit_payment_methods(),
    index=None,
)

st.divider()
st.subheader("Additional Information")
col1, col2 = st.columns(2)
rental_information['staff_name'] = col1.text_input("Staff Name")
rental_information['items_left_behind'] = col2.multiselect(
    "Items Left Behind by Renter",
    options=ItemLeftBehind,
)

st.divider()
st.subheader("Terms and Conditions")
st.markdown("insert bunch of conditions here...")

st.markdown("By signing below, I agree to the terms and conditions above.")
signature = st_canvas(
    stroke_width=2,
    stroke_color="#1E90FF",
    height=100,
)

# quick validation of renter agrement
signature = signature.image_data
allow_submission = all([
    np.count_nonzero(np.max(signature, axis=-1)) > 500,
    id_verified,
])

st.divider()
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
    args=(NewRental.model_construct(**rental_information), signature),
    disabled=not allow_submission,
)
