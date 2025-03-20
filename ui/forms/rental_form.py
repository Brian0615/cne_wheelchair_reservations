from typing import List

import streamlit as st

from common.constants import DeviceType, Location, WALK_IN_RESERVATION_ID, PaymentMethod, HoldItem
from ui.forms.base_form import BaseForm
from ui.forms.form_fields import (
    ButtonField,
    CheckboxField,
    DateField,
    MultiSelectField,
    SelectboxField,
    TextField,
    TimeField,
    SignatureField,
)


class RentalForm(BaseForm):
    """Form for creating a new rental"""

    def __init__(self, key_prefix: str):

        # load options from session state
        fee_payment_amount = st.session_state.get(f"{key_prefix}_fee_payment_amount", 0)
        deposit_payment_amount = st.session_state.get(f"{key_prefix}_deposit_payment_amount", 0)
        reservation_options = st.session_state.get(f"{key_prefix}_reservations", [])
        device_id_options = st.session_state.get(f"{key_prefix}_available_devices", [])

        fields = {
            "date": DateField(key=f"{key_prefix}_date", label="Rental Date"),
            "pickup_time": TimeField(key=f"{key_prefix}_time", label="Pickup Time"),
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
            ),
            "device_id": SelectboxField(
                key=f"{key_prefix}_device_id",
                label="Assigned Chair/Scooter",
                options=sorted(device_id_options, key=lambda x: int(x[1:])),
            ),
            "name": TextField(key=f"{key_prefix}_name", label="Name"),
            "phone_number": TextField(key=f"{key_prefix}_phone_number", label="Phone Number"),
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
            "signature": SignatureField(key=f"{key_prefix}_signature", label="Signature"),
            "id_verified": CheckboxField(key=f"{key_prefix}_id_verified", label="ID Verified?"),
            "submit": ButtonField(
                key=f"{key_prefix}_submit",
                label="Submit",
            )
        }
        super().__init__(key_prefix=key_prefix, fields=fields)

    def update_device_options(self, device_ids: List[str]):
        """Update the device options in the rental form"""
        if sorted(device_ids) != self.fields["device_id"].options:
            self.fields["device_id"].options = sorted(device_ids)
            st.write("updated devices")
        st.rerun()

    # pylint: disable=too-many-statements
    def render_form(self):

        result = {}

        # Intro Section of Rental Form
        with st.container(border=True):
            # first row of form
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                result["date"] = self.fields["date"].render()
            with col2:
                result["pickup_time"] = self.fields["pickup_time"].render()
            with col3:
                result["pickup_location"] = self.fields["pickup_location"].render()
            with col4:
                result["device_type"] = self.fields["device_type"].render()

            if not all(result.get(x) for x in result):
                return result, False

            # second row of form
            col1, col2, _, _ = st.columns(4)
            with col1:
                result["reservation_id"] = self.fields["reservation_id"].render()
            with col2:
                result["device_id"] = self.fields["device_id"].render()

            if not self.fields["device_id"].options:
                return result, False

        # Renter Information Section of Form
        with st.container(border=True):
            st.header("Renter Information")
            col1, col2 = st.columns([2, 1])
            with col1:
                result["name"] = self.fields["name"].render()
            with col2:
                result["phone_number"] = self.fields["phone_number"].render()

            col1, col2 = st.columns([2, 1])
            with col1:
                result["address"] = self.fields["address"].render()
            with col2:
                result["city"] = self.fields["city"].render()

            col1, col2, col3 = st.columns(3)
            with col1:
                result["province"] = self.fields["province"].render()
            with col2:
                result["postal_code"] = self.fields["postal_code"].render()
            with col3:
                result["country"] = self.fields["country"].render()

            result["id_verified"] = self.fields["id_verified"].render()

        # Payment Information Section of Form
        with st.container(border=True):
            st.subheader("Payment Information")
            col1, col2 = st.columns(2)
            with col1:
                result["fee_payment_amount"] = DeviceType.get_fee_amount(device=result["device_type"])
                result["fee_payment_method"] = self.fields["fee_payment_method"].render()
            with col2:
                result["deposit_payment_amount"] = DeviceType.get_deposit_amount(device=result["device_type"])
                result["deposit_payment_method"] = self.fields["deposit_payment_method"].render()

        # Additional Information Section of Form
        with st.container(border=True):
            st.subheader("Additional Information")
            col1, col2 = st.columns(2)
            with col1:
                result["staff_name"] = self.fields["staff_name"].render()
            with col2:
                result["items_left_behind"] = self.fields["items_left_behind"].render()

        # Terms and Conditions Section of Form
        with st.container(border=True):
            st.subheader("Terms and Conditions")
            st.markdown("Insert Terms and Conditions here...")
            st.markdown("By signing below, I agree to the terms and conditions above.")
            result["signature"] = self.fields["signature"].render()

        is_submitted = self.fields["submit"].render()

        return result, is_submitted
