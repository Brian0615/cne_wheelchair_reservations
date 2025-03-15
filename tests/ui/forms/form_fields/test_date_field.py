from unittest import TestCase

from streamlit.testing.v1 import AppTest

from ui.src.constants import CNEDates


class TestDateField(TestCase):

    def test_initialize_field(self):
        """Test initializing a new Date Field"""

        def run_initialize_field():
            from ui.forms.form_fields.date_field import DateField
            field = DateField(key="test_key", label="Test Label")
            field.initialize_field()

        at = AppTest.from_function(run_initialize_field).run()
        self.assertEqual(at.session_state["test_key"], CNEDates.get_default_date())

    def test_render(self):
        """Test rendering a Date field"""

        def run_render(is_disabled: bool):
            from ui.forms.form_fields.date_field import DateField
            field = DateField(key="test_key", label="Test Label")
            field.initialize_field()
            field.render(disabled=is_disabled)

        for disabled in [True, False]:
            with self.subTest(f"Render with disabled={disabled}"):
                at = AppTest.from_function(run_render, kwargs={"is_disabled": disabled}).run()

                self.assertEqual(at.date_input("test_key").disabled, disabled)
                self.assertEqual(at.date_input("test_key").min, min(CNEDates.get_cne_date_list()))
                self.assertEqual(at.date_input("test_key").max, max(CNEDates.get_cne_date_list()))
                self.assertEqual(at.date_input("test_key").label, "Test Label")
                self.assertEqual(at.date_input("test_key").value, CNEDates.get_default_date())
