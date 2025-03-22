import streamlit as st

from ui.forms.form_fields.base_form_field import BaseFormField


class CheckboxField(BaseFormField):
    """Checkbox field class"""

    def __init__(self, key: str, label: str):
        super().__init__(key=key, label=label)

    def _initialize(self):
        """Initialize the checkbox field - do nothing as checkboxes cannot be initialized"""

    def _render(self, disabled: bool = False):
        """Render the checkbox field"""
        return st.checkbox(label=self.label, key=self.key, disabled=disabled)
