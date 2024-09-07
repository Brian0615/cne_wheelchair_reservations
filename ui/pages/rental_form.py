import streamlit as st
from streamlit_drawable_canvas import st_canvas

from common.constants import DeviceType, Location, PaymentMethod

st.set_page_config(layout="wide")
st.header("Rental Form")

col1, col2, col3 = st.columns([2, 1, 1])
rental_type = col1.selectbox("Rental Type", options=DeviceType, index=None)
assigned_device = col2.selectbox("Assigned Chair/Scooter", options=["WC1"], index=None)
rental_location = col3.selectbox("Rental Location", options=Location, index=None)
st.divider()

st.subheader("Renter Information")

col1, col2, col3 = st.columns([2, 1, 1])
renter_name = col1.text_input(label="Name")
rental_date = col2.date_input(label="Date", value="today")
rental_time = col3.time_input(label="Time", value="now")

address = st.text_input(label="Address")
col1, col2, col3 = st.columns([2, 1, 1])
city = col1.text_input(label="City")
province = col2.text_input(label="Province")
postal_code = col3.text_input(label="Postal Code")

st.checkbox("ID Verified?")

if rental_type is not None:
    st.divider()
    st.subheader("Payment Information")
    col1, col2 = st.columns(2)
    fee_payment_type = col1.selectbox(
        label=f"Payment Type for **${DeviceType.get_fee_amount(rental_type)}** Fee",
        options=PaymentMethod,
        index=None,
    )
    deposit_payment_type = col2.selectbox(
        label=f"Payment Type for **${DeviceType.get_deposit_amount(rental_type)}** Deposit",
        options=PaymentMethod,
        index=None,
    )

    st.divider()
    st.subheader("Additional Information")
    col1, col2 = st.columns(2)
    staff_name = col1.text_input("Staff Name")
    items = col2.multiselect(
        "Items Left Behind by Renter",
        options=["Cane", "Crutches", "Stroller", "Walker", "Wheelchair"],
    )

    st.divider()
    st.subheader("Terms and Conditions")
    st.markdown("insert bunch of conditions here...")

    st.markdown("Signature")
    # pylint: disable=invalid-name
    signature = st_canvas(
        stroke_width=2,
        stroke_color="#1E90FF",
        height=100,
    )
