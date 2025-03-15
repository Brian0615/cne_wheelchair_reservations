from datetime import time, timedelta
from typing import Optional

import streamlit as st

from ui.forms.form_fields.base_form_field import BaseFormField


# pylint: disable=too-few-public-methods, too-many-arguments
class TimeField(BaseFormField):
    """Time field class"""

    def __init__(
            self,
            key: str,
            label: Optional[str] = "Time",
            default_value: Optional[time] = time(hour=10),
            step: Optional[timedelta] = timedelta(minutes=30),
    ):
        self.step = step
        super().__init__(key=key, label=label, default_value=default_value)

    def render(self, disabled: bool = False):
        """Render the time field"""
        return st.time_input(label=self.label, key=self.key, step=self.step, disabled=disabled)
