import re

import streamlit as st

from common.constants import DeviceType, Location, WALK_IN_RESERVATION_ID, PaymentMethod, HoldItem
from ui.forms.base_form import BaseForm
from ui.forms.form_fields import (
    ButtonField,
    CheckboxField,
    DateField,
    MultiSelectField,
    PhoneNumberField,
    SelectboxField,
    TextField,
    TimeField,
)


# pylint: disable=too-few-public-methods
class NewRentalForm(BaseForm):
    """Form for creating a new rental"""

    def __init__(self, key_prefix: str):

        # load options from session state
        fee_payment_amount = st.session_state.get(f"{key_prefix}_fee_payment_amount", 0)
        deposit_payment_amount = st.session_state.get(f"{key_prefix}_deposit_payment_amount", 0)
        reservation_options = st.session_state.get(f"{key_prefix}_reservations", [])
        device_id_options = st.session_state.get(f"{key_prefix}_available_devices", [])

        fields = {
            "date": DateField(key=f"{key_prefix}_date", label="Rental Date"),
            "pickup_time": TimeField(
                key=f"{key_prefix}_time",
                label="Pickup Time (24-hour format)",
            ),
            "pickup_location": SelectboxField(
                key=f"{key_prefix}_pickup_location",
                label="Pickup Location",
                options=Location,
            ),
            "device_type": SelectboxField(
                key=f"{key_prefix}_device_type",
                label="Rental Type",
                options=DeviceType,
            ),
            "reservation_id": SelectboxField(
                key=f"{key_prefix}_reservation_id",
                label="Reservation Name/ID",
                options=reservation_options + [WALK_IN_RESERVATION_ID],
                default_value=st.session_state.get(f"{key_prefix}_reservation_id", None),
            ),
            "device_id": SelectboxField(
                key=f"{key_prefix}_device_id",
                label="Assigned Chair/Scooter",
                options=sorted(device_id_options, key=lambda x: int(x[1:])),
                default_value=st.session_state.get(f"{key_prefix}_device_id", None),
            ),
            "name": TextField(key=f"{key_prefix}_name", label="Name"),
            "phone_number": PhoneNumberField(key=f"{key_prefix}_phone_number", label="Phone Number"),
            "address": TextField(key=f"{key_prefix}_address", label="Address"),
            "city": TextField(key=f"{key_prefix}_city", label="City"),
            "province": TextField(key=f"{key_prefix}_province", label="Province", default_value="Ontario"),
            "postal_code": TextField(key=f"{key_prefix}_postal_code", label="Postal Code"),
            "country": TextField(key=f"{key_prefix}_country", label="Country", default_value="Canada"),
            "fee_payment_method": SelectboxField(
                key=f"{key_prefix}_fee_payment_method",
                label=f"Payment Type for **${fee_payment_amount}** Fee",
                options=PaymentMethod.get_accepted_fee_payment_methods(),
            ),
            "deposit_payment_method": SelectboxField(
                key=f"{key_prefix}_deposit_payment_method",
                label=f"Payment Type for **${deposit_payment_amount}** Deposit",
                options=PaymentMethod.get_accepted_deposit_payment_methods(),
            ),
            "staff_name": TextField(key=f"{key_prefix}_staff_name", label="Staff Name"),
            "items_left_behind": MultiSelectField(
                key=f"{key_prefix}_items_left_behind",
                label="Items Left Behind by Renter",
                options=HoldItem,
            ),
            "id_verified": CheckboxField(key=f"{key_prefix}_id_verified", label="ID Verified?"),
            "submit": ButtonField(
                key=f"{key_prefix}_submit",
                label="Submit",
            )
        }
        super().__init__(key_prefix=key_prefix, fields=fields)

    # pylint: disable=too-many-statements
    def render_form(self):

        result = {}

        # Intro Section of Rental Form
        with st.container(border=True):
            # first row of form
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                result["date"] = self.fields["date"].render_field()
            with col2:
                result["pickup_time"] = self.fields["pickup_time"].render_field()
            with col3:
                result["pickup_location"] = self.fields["pickup_location"].render_field()
            with col4:
                result["device_type"] = self.fields["device_type"].render_field()

            if not all(result.get(x) for x in result):
                return result, False

            # second row of form
            col1, col2, _ = st.columns([2, 1, 1])
            with col1:
                result["reservation_id"] = self.fields["reservation_id"].render_field()
            if result["reservation_id"] and result["reservation_id"] != WALK_IN_RESERVATION_ID:
                result["reservation_id"] = re.search(r"\(([^)]+)\)", result["reservation_id"]).group(1)
            with col2:
                result["device_id"] = self.fields["device_id"].render_field()

            if not self.fields["device_id"].options:
                return result, False

        # Renter Information Section of Form
        with st.container(border=True):
            st.subheader("Renter Information")
            col1, col2 = st.columns([2, 1])
            with col1:
                result["name"] = self.fields["name"].render_field()
            with col2:
                result["phone_number"] = self.fields["phone_number"].render_field()

            col1, col2 = st.columns([2, 1])
            with col1:
                result["address"] = self.fields["address"].render_field()
            with col2:
                result["city"] = self.fields["city"].render_field()

            col1, col2, col3 = st.columns(3)
            with col1:
                result["province"] = self.fields["province"].render_field()
            with col2:
                result["postal_code"] = self.fields["postal_code"].render_field()
            with col3:
                result["country"] = self.fields["country"].render_field()

            result["id_verified"] = self.fields["id_verified"].render_field()

        # Payment Information Section of Form
        with st.container(border=True):
            st.subheader("Payment Information")
            col1, col2 = st.columns(2)
            with col1:
                result["fee_payment_amount"] = DeviceType.get_fee_amount(device=result["device_type"])
                result["fee_payment_method"] = self.fields["fee_payment_method"].render_field()
            with col2:
                result["deposit_payment_amount"] = DeviceType.get_deposit_amount(device=result["device_type"])
                result["deposit_payment_method"] = self.fields["deposit_payment_method"].render_field()

        # Additional Information Section of Form
        with st.container(border=True):
            st.subheader("Additional Information")
            col1, col2 = st.columns(2)
            with col1:
                result["staff_name"] = self.fields["staff_name"].render_field()
            with col2:
                result["items_left_behind"] = self.fields["items_left_behind"].render_field()

        is_submitted = self.fields["submit"].render_field()

        return result, is_submitted
