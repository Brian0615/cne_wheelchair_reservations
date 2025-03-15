from unittest import TestCase

from streamlit.testing.v1 import AppTest


class TestTextField(TestCase):

    def test_initialize_field(self):
        """Test initializing a new Text Field"""

        def run_initialize_field(default_value):
            from ui.forms.form_fields.text_field import TextField
            field = TextField(key="test_key", label="Test Label", default_value=default_value)
            field.initialize_field()

        for default in [None, "b"]:
            with self.subTest(msg=f"Default value={default}"):
                at = AppTest.from_function(run_initialize_field, kwargs={"default_value": default}).run()
                self.assertEqual(at.session_state["test_key"], default)

    def test_render(self):
        """Test rendering a Text field"""

        def run_render(default_value, is_disabled: bool):
            from ui.forms.form_fields.text_field import TextField
            field = TextField(key="test_key", label="Test Label", default_value=default_value)
            field.initialize_field()
            field.render(disabled=is_disabled)

        for disabled in [True, False]:
            for default in [None, "b"]:
                with self.subTest(f"Render with default_value={default}, disabled={disabled}"):
                    at = AppTest.from_function(run_render, kwargs={"default_value": default, "is_disabled": disabled})
                    at.run()

                    self.assertEqual(at.text_input("test_key").disabled, disabled)
                    self.assertEqual(at.text_input("test_key").label, "Test Label")
                    self.assertEqual(at.text_input("test_key").value, default)

                    if not disabled:
                        at.text_input("test_key").input("abcdef")
                        at.run()
                        self.assertEqual(at.text_input("test_key").value, "abcdef")
