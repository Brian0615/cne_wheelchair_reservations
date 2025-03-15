from unittest import TestCase

from streamlit.testing.v1 import AppTest


class TestBaseFormField(TestCase):

    def test_initialize_field(self):
        """Test initializing a new Form Field"""

        def run_newly_initialized_field():
            from ui.forms.form_fields.base_form_field import BaseFormField
            field = BaseFormField(key="test_key", label="Test Label", default_value="Test Value")
            field.initialize_field()

        def run_previously_initialized_field():
            import streamlit as st

            from ui.forms.form_fields.base_form_field import BaseFormField

            st.session_state["test_key"] = "Test Value"
            field = BaseFormField(key="test_key", label="Test Label", default_value="Test Value New")
            field.initialize_field()

        with self.subTest(msg="Newly initialized field"):
            at = AppTest.from_function(run_newly_initialized_field).run()
            self.assertEqual(at.session_state["test_key"], "Test Value")

        with self.subTest(msg="Previously initialized field"):
            at = AppTest.from_function(run_previously_initialized_field).run()
            self.assertEqual(at.session_state["test_key"], "Test Value")

    def test_clear_field(self):
        """Test clearing a Form Field"""

        def run_clear_field():
            from ui.forms.form_fields.base_form_field import BaseFormField

            field = BaseFormField(key="test_key", label="Test Label", default_value="Test Value")
            field.clear_field()

        at = AppTest.from_function(run_clear_field).run()
        with self.assertRaises(KeyError):
            _ = at.session_state["test_key"]

    def test_render_field(self):

        def run_render_field():
            from ui.forms.form_fields.base_form_field import BaseFormField

            field = BaseFormField(key="test_key", label="Test Label", default_value="Test Value")
            field.render()

        # note: this error would not be explicitly raised because it is raised inside the AppTest
        at = AppTest.from_function(run_render_field).run()
        self.assertEqual(at.exception[0].proto.type, "NotImplementedError")
