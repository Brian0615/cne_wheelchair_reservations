from streamlit.testing.v1 import AppTest

from tests.unit.base_tests import BaseTestCases
from ui.forms.form_fields.phone_number_field import PhoneNumberField


class TestPhoneNumberField(BaseTestCases.BaseFormFieldTest):
    """Tests for PhoneNumberField."""

    def setUp(self):
        self.field_class = PhoneNumberField
        self.expected_init_value = None

    @staticmethod
    def _get_field(at: AppTest):
        return at.text_input("test_key")

    def test_initialize_field(self):
        super()._test_initialize_field_without_kwargs()

    def test_tel_prefix_stripped_from_default_value(self):
        """PhoneNumberField strips the 'tel:' prefix from the default value."""
        at = AppTest.from_function(
            script=self._run_field,
            args=(self.field_class,),
            kwargs={"default_value": "tel:+1-416-820-2370"},
        ).run()
        self.assertEqual("+1-416-820-2370", at.session_state["test_key"])

    def test_default_value_without_prefix_unchanged(self):
        """A default value without 'tel:' is stored as-is."""
        at = AppTest.from_function(
            script=self._run_field,
            args=(self.field_class,),
            kwargs={"default_value": "4168202370"},
        ).run()
        self.assertEqual("4168202370", at.session_state["test_key"])

    def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
        self.assertEqual(self._get_field(at=at).value, None)

    def _run_field_post_interaction_checks(self, at: AppTest):
        self._get_field(at=at).input("9052938402")
        at.run()
        self.assertEqual(self._get_field(at=at).value, "9052938402")
