from enum import StrEnum
from typing import List, Optional, Type, Union

import streamlit as st

from ui.forms.form_fields.base_form_field import BaseFormField


# pylint: disable=too-few-public-methods
class MultiSelectField(BaseFormField):
    """MultiSelect field class"""

    def __init__(
            self,
            key: str,
            label: str,
            options: Union[List[str], Type[StrEnum]],
            default_value: Optional[str] = None,
    ):
        self.options = options
        super().__init__(key=key, label=label, default_value=default_value if default_value else [])

    def render(self, disabled: bool = False):
        """Render the MultiSelect field"""
        return st.multiselect(
            label=self.label,
            options=self.options,
            key=self.key,
            disabled=disabled,
        )
