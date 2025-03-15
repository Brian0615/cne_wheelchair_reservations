from typing import Any, Optional

import streamlit as st


class BaseFormField:
    """Base class for form fields"""

    def __init__(self, key: str, label: str, default_value: Optional[Any] = None):
        self.key = key
        self.label = label
        self.default_value = default_value

    def initialize_field(self):
        """Initialize the form field"""
        if self.key not in st.session_state:
            st.session_state[self.key] = self.default_value

    def clear_field(self):
        """Clear the form field"""
        if self.key in st.session_state:
            del st.session_state[self.key]

    def render(self, disabled: bool = False):
        """Render the form field"""
        raise NotImplementedError("Method `render` must be implemented in a subclass")
