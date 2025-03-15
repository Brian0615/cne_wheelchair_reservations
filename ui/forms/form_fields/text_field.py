from typing import Optional

import streamlit as st

from ui.forms.form_fields.base_form_field import BaseFormField


# pylint: disable=too-few-public-methods
class TextField(BaseFormField):
    """Text input field class"""

    def __init__(
            self,
            key: str,
            label: str,
            default_value: Optional[str] = None,
    ):
        super().__init__(key=key, label=label, default_value=default_value)

    def render(self, disabled=False):
        """Render the text input field"""
        return st.text_input(label=self.label, key=self.key, disabled=disabled)
