from streamlit_drawable_canvas import st_canvas

from ui.forms.form_fields.base_form_field import BaseFormField


# pylint: disable=too-few-public-methods
class SignatureField(BaseFormField):
    """Signature field class"""

    def render(self, disabled: bool = False):
        """Render the signature field"""
        return st_canvas(
            stroke_width=2,
            stroke_color="#1E90FF",
            height=100,
            key=self.key,
        ).image_data
