from typing import Any, Dict, Tuple

from ui.forms.form_fields import FormField


class BaseForm:
    """Base form class"""

    def __init__(self, key_prefix: str, fields: Dict[str, FormField]):
        self.key_prefix = key_prefix
        self.fields = fields

    def clear_form(self):
        """Clear the form"""
        for field in self.fields.values():
            field.clear_field()

    def initialize_form(self):
        """Initialize the form"""
        for field in self.fields.values():
            field.initialize_field()

    def render_form(self) -> Tuple[Dict[str, Any], bool]:
        """Render the form"""
        raise NotImplementedError("Method `render_form` must be implemented in a subclass")
