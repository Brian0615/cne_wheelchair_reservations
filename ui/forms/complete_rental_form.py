from datetime import timedelta
from typing import Tuple, Dict, Any

import streamlit as st

from common.constants import DeviceType, Location
from common.data_models import RentalSummary
from ui.forms.base_form import BaseForm
from ui.forms.form_fields import (
    ButtonField,
    CheckboxField,
    DateField,
    TimeField,
    SelectboxField,
    TextField,
)


# pylint: disable=too-few-public-methods
class CompleteRentalForm(BaseForm):
    """Form for completing a rental"""

    def __init__(self, key_prefix: str, rental_info: RentalSummary):
        self.rental_info = rental_info

        fields = {
            "return_date": DateField(
                key=f"{key_prefix}_return_date",
                label="Return Date",
                default_value=self.rental_info.date,
            ),
            "return_time": TimeField(
                key=f"{key_prefix}_return_time",
                label="Return Time (24-hour format)",
                step=timedelta(minutes=15),
            ),
            "return_location": SelectboxField(
                key=f"{key_prefix}_return_location",
                label="Return Location",
                options=Location,
            ),
            "return_staff_name": TextField(key=f"{key_prefix}_staff_name", label="Staff Name"),
            "deposit_received": CheckboxField(
                key=f"{key_prefix}_deposit_received",
                label=f"{self.rental_info.deposit_payment_method} Deposit of "
                      f"${DeviceType.get_deposit_amount(self.rental_info.device_type)}",
            ),
            "submit": ButtonField(key=f"{key_prefix}_submit", label="Complete Rental"),
        }
        if self.rental_info.items_left_behind:
            fields["items_left_behind"] = CheckboxField(
                key=f"{key_prefix}_items_left_behind",
                label="Items Left Behind during Rental: " + ", ".join(self.rental_info.items_left_behind),
            )
        super().__init__(fields=fields, key_prefix=key_prefix)

    def render_form(self) -> Tuple[Dict[str, Any], bool]:
        """Render the form"""

        result = {}
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                result["return_date"] = self.fields["return_date"].render_field()
            with col2:
                result["return_time"] = self.fields["return_time"].render_field()
            with col3:
                result["return_location"] = self.fields["return_location"].render_field()
            with col4:
                result["return_staff_name"] = self.fields["return_staff_name"].render_field()

            st.write("**Please confirm below that the following have been returned to the renter:**")

            check_items = True
            if self.rental_info.items_left_behind:
                check_items = self.fields["items_left_behind"].render_field()
            check_deposit = self.fields["deposit_received"].render_field()
            result["check_items_deposit"] = check_items and check_deposit

            is_submitted = self.fields["submit"].render_field(
                disabled=any([
                    not result["return_date"],
                    not result["return_time"],
                    not result["return_location"],
                    not result["return_staff_name"],
                    not result["check_items_deposit"],
                ])
            )

            return result, is_submitted
