from enum import StrEnum
from typing import List, Optional, Type, Union

import streamlit as st

from ui.forms.form_fields.base_form_field import BaseFormField


# pylint: disable=too-few-public-methods
class SelectboxField(BaseFormField):
    """Selectbox field class"""

    def __init__(
            self,
            key: str,
            label: str,
            options: Union[List[str], Type[StrEnum]],
            default_value: Optional[str] = None,
    ):
        self.options = options
        super().__init__(key=key, label=label, default_value=default_value if default_value else None)

    def _render(self, disabled: bool = False):
        """Render the selectbox field"""
        return st.selectbox(
            label=self.label,
            options=self.options,
            index=self.options.index(self.default_value) if self.default_value in self.options else None,
            key=self.key,
            disabled=disabled,
        )
