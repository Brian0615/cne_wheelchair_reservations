from typing import Optional

import streamlit as st

from ui.forms.form_fields.text_field import TextField


# pylint: disable=too-few-public-methods
class PhoneNumberField(TextField):
    """Text input field class"""

    def __init__(
            self,
            key: str,
            label: str,
            default_value: Optional[str] = None,
    ):
        super().__init__(key=key, label=label, default_value=default_value)

    def _render(self, disabled=False):
        """Render the text input field"""
        return st.text_input(
            label=self.label,
            key=self.key,
            disabled=disabled,
            placeholder="e.g. +1 123-456-7890",
            help="**Canada/US**: country code (+1) not required \n\n "
                 "**International**: include country code (e.g. +44 for UK)"
        )
