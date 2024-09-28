from datetime import datetime, time

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
from ui.src.utils import display_validation_errors, encode_signature_base64

st.set_page_config(layout="wide")
data_service = DataService()


def clear_rental_form(key_prefix: str) -> None:
    """Clear session state data with a given key prefix"""
    for key in st.session_state.keys():
        if key.startswith(key_prefix):
            if key.endswith("date"):
                st.session_state[key] = CNEDates.get_default_date(),
            elif key.endswith("pickup_time"):
                st.session_state[key] = datetime.now(tz=pytz.timezone("America/Toronto")).time()
            else:
                st.session_state[key] = None


@st.dialog("Success!")
def display_success_dialog(rental_id: str, new_rental: NewRental):
    st.success(
        f"""
        The following rental was created successfully:
        
        * **Name**: {new_rental.name}
        * **{new_rental.device_type}**: {new_rental.device_id}
        * **Rental ID**: {rental_id}
        """
    )
    if st.button("Close"):
        clear_rental_form(key_prefix="rental_form_")  # clear rental form for next rental
        st.rerun()


def submit_form(new_rental: NewRental, signature: np.array):
    # clear previous errors
    st.session_state["rental_form_errors"] = None
    try:
        # process signature
        signature = Image.fromarray(signature)
        new_rental.signature = encode_signature_base64(signature)

        # update pickup time
        if isinstance(new_rental.pickup_time, time):
            new_rental.pickup_time = datetime.combine(
                date=new_rental.date,
                time=new_rental.pickup_time,
                tzinfo=pytz.timezone("America/Toronto"),
            )

        # validate rental data
        new_rental = NewRental(**new_rental.model_dump())

        # try to add the new rental
        status_code, result = data_service.add_new_rental(new_rental)
        if status_code == 200:
            display_success_dialog(rental_id=result, new_rental=new_rental)

    except ValidationError as exc:
        st.session_state["rental_form_errors"] = exc.errors()


st.header("Start a New Rental")
rental_information = {}

# first row of intro section of form
col1, col2, col3, col4 = st.columns(4)
all_dates = CNEDates.get_cne_date_list(year=datetime.today().year)
rental_information["date"] = col1.date_input(
    label="Rental Date",
    min_value=min(all_dates),
    max_value=max(all_dates),
    value=CNEDates.get_default_date(),
    key="rental_form_date",
)
rental_information["pickup_time"] = col2.time_input(label="Pickup Time", value="now", key="rental_form_pickup_time")
rental_information["pickup_location"] = col3.selectbox(
    label="Pickup Location",
    options=Location,
    index=None,
    key="rental_form_pickup_location",
)
rental_information["device_type"] = col4.selectbox(
    label="Rental Type",
    options=DeviceType,
    index=None,
    key="rental_form_device_type",
)

if not all(rental_information.get(x) for x in ["date", "pickup_time", "pickup_location", "device_type"]):
    st.stop()

# check whether there are available devices
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

# second row of intro section of form
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
    key="rental_form_reservation_id",
)
if rental_information["reservation_id"]:
    if rental_information["reservation_id"] != WALK_IN_RESERVATION_ID:
        rental_information["reservation_id"] = rental_information["reservation_id"].split("(")[1].replace(")", "")
    else:
        rental_information["reservation_id"] = None

rental_information["device_id"] = col2.selectbox(
    "Assigned Chair/Scooter",
    options=available_devices,
    index=None,
    key="rental_form_device_id",
)

# renter information section of form
st.divider()
st.subheader("Renter Information")
col1, col2 = st.columns([2, 1])
rental_information["name"] = col1.text_input(label="Name", key="rental_form_name")
rental_information["phone_number"] = col2.text_input(label="Phone Number", key="rental_form_phone_number")

col1, col2 = st.columns([2, 1])
rental_information['address'] = col1.text_input(label="Address", key="rental_form_address")
rental_information['city'] = col2.text_input(label="City", key="rental_form_city")
col1, col2, col3 = st.columns(3)
rental_information['province'] = col1.text_input(label="Province", value="Ontario", key="rental_form_province")
rental_information['postal_code'] = col2.text_input(label="Postal Code", key="rental_form_postal_code")
rental_information['country'] = col3.text_input(label="Country", value="Canada", key="rental_form_country")

id_verified = st.checkbox("ID Verified?")

st.divider()
st.subheader("Payment Information")
col1, col2 = st.columns(2)
rental_information["fee_payment_amount"] = DeviceType.get_fee_amount(rental_information["device_type"])
rental_information['fee_payment_method'] = col1.selectbox(
    label=f"Payment Type for **${rental_information['fee_payment_amount']}** Fee",
    options=PaymentMethod.get_accepted_fee_payment_methods(),
    index=None,
    key="rental_form_fee_payment_method",
)
rental_information["deposit_payment_amount"] = DeviceType.get_deposit_amount(rental_information["device_type"])
rental_information['deposit_payment_method'] = col2.selectbox(
    label=f"Payment Type for **${rental_information['deposit_payment_amount']}** Deposit",
    options=PaymentMethod.get_accepted_deposit_payment_methods(),
    index=None,
    key="rental_form_deposit_payment_method",
)

st.divider()
st.subheader("Additional Information")
col1, col2 = st.columns(2)
rental_information['staff_name'] = col1.text_input("Staff Name")
rental_information['items_left_behind'] = col2.multiselect(
    "Items Left Behind by Renter",
    options=ItemLeftBehind,
    key="rental_form_items_left_behind",
)

st.divider()
st.subheader("Terms and Conditions")
st.markdown("insert bunch of conditions here...")

st.markdown("By signing below, I agree to the terms and conditions above.")
canvas_signature = st_canvas(
    stroke_width=2,
    stroke_color="#1E90FF",
    height=100,
    key="rental_form_signature",
)

# quick validation of renter agreement
canvas_signature = canvas_signature.image_data
allow_submission = all([
    np.count_nonzero(np.max(canvas_signature, axis=-1)) > 500,
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
    args=(NewRental.model_construct(**rental_information), canvas_signature),
    disabled=not allow_submission,
)
