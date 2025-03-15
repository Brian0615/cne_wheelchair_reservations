from unittest import TestCase

from streamlit.testing.v1 import AppTest


class TestButtonField(TestCase):

    def test_initialize_field(self):
        """Test initializing a new Button Field"""

        def run_initialize_field():
            from ui.forms.form_fields.button_field import ButtonField
            field = ButtonField(key="test_key", label="Test Label")
            field.initialize_field()

        at = AppTest.from_function(run_initialize_field).run()
        with self.assertRaises(KeyError, msg="Button fields should not have any initialization"):
            _ = at.session_state["test_key"]

    def test_render(self):
        """Test rendering a Button field"""

        def run_render(is_disabled: bool):
            from ui.forms.form_fields.button_field import ButtonField
            field = ButtonField(key="test_key", label="Test Label")
            field.initialize_field()
            field.render(disabled=is_disabled)

        for disabled in [True, False]:
            with self.subTest(f"Render with disabled={disabled}"):
                at = AppTest.from_function(run_render, kwargs={"is_disabled": disabled}).run()

                # check that button exists and is enabled/disabled given the input
                self.assertEqual(at.button("test_key").disabled, disabled)
                self.assertEqual(at.button("test_key").label, "Test Label")
                self.assertFalse(at.button("test_key").value)

                # test click
                if not disabled:
                    at.button("test_key").click()
                    at.run()
                    self.assertTrue(at.button("test_key").value)
