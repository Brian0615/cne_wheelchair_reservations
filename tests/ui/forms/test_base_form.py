from unittest import TestCase

from streamlit.testing.v1 import AppTest

from ui.forms.base_form import BaseForm
from ui.forms.form_fields import ButtonField, SelectboxField, TextField


class TestBaseForm(TestCase):

    def setUp(self):
        self.form = BaseForm(
            key_prefix="test_form",
            fields={
                "selectbox_field": SelectboxField(
                    key="selectbox_field",
                    label="Selectbox Field",
                    options=["option1", "option2"],
                ),
                "text_field": TextField(key="text_field", label="Text Field"),
                "button_field": ButtonField(key="button_field", label="Button Field"),
            },
        )

    def test_initialize_form(self):
        """Test initializing the form"""

        def run_initialize_form(form):
            form.initialize_form()

        # check that the session state is initialized properly
        at = AppTest.from_function(run_initialize_form, kwargs={"form": self.form}).run()
        for field in ["selectbox_field", "text_field"]:
            self.assertEqual(at.session_state[field], None, msg=f"Field {field} should be initialized to None")

    def test_clear_form(self):
        """Test clearing the form"""

        def run_clear_form(form):
            form.initialize_form()
            form.clear_form()

        # check that the fields get cleared
        at = AppTest.from_function(run_clear_form, kwargs={"form": self.form}).run()
        for field in ["selectbox_field", "text_field"]:
            with self.assertRaises(KeyError, msg=f"Field {field} should be cleared from session state"):
                _ = at.session_state[field]

    def test_render_form(self):
        """Test rendering the form - this method should raise a NotImplementedError"""

        def run_render_form(form):
            form.initialize_form()
            form.render_form()

        # note: this error would not be explicitly raised because it is raised inside the AppTest
        at = AppTest.from_function(run_render_form, kwargs={"form": self.form}).run()
        self.assertEqual(at.exception[0].proto.type, "NotImplementedError")
