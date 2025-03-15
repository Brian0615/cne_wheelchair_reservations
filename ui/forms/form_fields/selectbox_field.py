from typing import List, Optional

import streamlit as st

from ui.forms.form_fields.base_form_field import BaseFormField


# pylint: disable=too-few-public-methods
class SelectboxField(BaseFormField):
    """Selectbox field class"""

    def __init__(
            self,
            key: str,
            label: str,
            options: List[str],
            default_value: Optional[str] = None,
    ):
        self.options = options
        super().__init__(key=key, label=label, default_value=default_value if default_value else None)

    def render(self, disabled: bool = False):
        """Render the selectbox field"""
        return st.selectbox(
            label=self.label,
            options=self.options,
            key=self.key,
            disabled=disabled,
        )
