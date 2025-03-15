from datetime import time
from typing import Optional

import streamlit as st

from common.constants import DeviceType, Location
from common.data_models import Reservation
from ui.forms.base_form import BaseForm
from ui.forms.form_fields import ButtonField, DateField, SelectboxField, TextField, TimeField
from ui.src.constants import CNEDates


# pylint: disable=too-few-public-methods
class ReservationForm(BaseForm):
    """Form for creating a new reservation or updating an existing reservation"""

    def __init__(self, key_prefix: str, existing_reservation: Optional[Reservation] = None, disabled: bool = False):
        self.disabled = disabled
        self.existing_reservation = existing_reservation
        fields = {
            "date": DateField(
                key=f"{key_prefix}_date",
                label="Reservation Date",
                default_value=(
                    existing_reservation.date if existing_reservation else CNEDates.get_default_new_reservation_date()
                ),
            ),
            "device_type": SelectboxField(
                key=f"{key_prefix}_device_type",
                label="Device Type",
                options=list(DeviceType),
                default_value=existing_reservation.device_type if existing_reservation else None,
            ),
            "location": SelectboxField(
                key=f"{key_prefix}_location",
                label="Location",
                options=list(Location),
                default_value=existing_reservation.location if existing_reservation else None
            ),
            "name": TextField(
                key=f"{key_prefix}_name",
                label="Name",
                default_value=existing_reservation.name if existing_reservation else None
            ),
            "phone_number": TextField(
                key=f"{key_prefix}_phone_number",
                label="Phone Number",
                default_value=existing_reservation.phone_number if existing_reservation else None
            ),
            "reservation_time": TimeField(
                key=f"{key_prefix}time",
                label="Reservation Time",
                default_value=existing_reservation.reservation_time if existing_reservation else time(hour=10)
            ),
            "notes": TextField(
                key=f"{key_prefix}_notes",
                label="Additional Notes",
                default_value=existing_reservation.notes if existing_reservation else None,
            ),
            "is_submitted": ButtonField(key=f"{key_prefix}_submit", label="Submit Reservation"),
        }
        super().__init__(key_prefix=key_prefix, fields=fields)

    def render_form(self):
        """Render the reservation form"""
        result = {}
        col1, col2, col3 = st.columns(3)
        with col1:
            result["date"] = self.fields["date"].render(disabled=self.disabled or self.existing_reservation)
        with col2:
            result["device_type"] = self.fields["device_type"].render(
                disabled=self.disabled or self.existing_reservation)
        with col3:
            result["location"] = self.fields["location"].render(disabled=self.disabled and self.existing_reservation)
        col1, col2, col3 = st.columns(3)
        with col1:
            result["name"] = self.fields["name"].render(disabled=self.disabled and self.existing_reservation)
        with col2:
            result["phone_number"] = self.fields["phone_number"].render(
                disabled=self.disabled and self.existing_reservation)
        with col3:
            result["reservation_time"] = self.fields["reservation_time"].render(
                disabled=self.disabled and self.existing_reservation)
        result["notes"] = self.fields["notes"].render(disabled=self.disabled and self.existing_reservation)
        st.divider()
        is_submitted = self.fields["is_submitted"].render(disabled=self.disabled and self.existing_reservation)
        return result, is_submitted
