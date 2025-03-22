from datetime import date
from typing import Optional

import streamlit as st

from ui.forms.form_fields.base_form_field import BaseFormField
from ui.src.constants import CNEDates


# pylint: disable=too-few-public-methods
class DateField(BaseFormField):
    """Date field class"""

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
            self,
            key: str,
            label: Optional[str] = "Date",
            default_value: Optional[date] = CNEDates.get_default_date(),
            min_date: Optional[date] = min(CNEDates.get_cne_date_list()),
            max_date: Optional[date] = max(CNEDates.get_cne_date_list()),
    ):
        self.min_date = min_date
        self.max_date = max_date
        super().__init__(key=key, label=label, default_value=default_value)

    def _render(self, disabled: bool = False):
        """Render the date field"""
        return st.date_input(
            label=self.label,
            key=self.key,
            min_value=self.min_date,
            max_value=self.max_date,
            disabled=disabled,
        )
