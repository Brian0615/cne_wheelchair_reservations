import streamlit as st

from ui.forms.form_fields.base_form_field import BaseFormField


# pylint: disable=too-few-public-methods
class ButtonField(BaseFormField):
    """Button field class"""

    def __init__(self, key: str, label: str):
        super().__init__(key=key, label=label)

    def initialize_field(self):
        """Initialize the button field - do nothing as buttons cannot be initialized"""

    def render(self, disabled: bool = False):
        """Render the button field"""
        return st.button(label=self.label, key=self.key, disabled=disabled)
