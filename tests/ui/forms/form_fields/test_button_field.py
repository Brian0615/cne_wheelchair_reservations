from streamlit.testing.v1 import AppTest

from tests.base_tests import BaseTestCases
from ui.forms.form_fields.button_field import ButtonField


class TestButtonField(BaseTestCases.BaseFormFieldTest):
    """Test the Button Field"""

    def setUp(self):
        self.field_class = ButtonField
        self.expected_init_value = None

    def test_initialize_field(self):
        """Test initializing a new Button Field"""

        at = AppTest.from_function(script=self._run_field, args=(self.field_class,)).run()
        with self.assertRaises(KeyError, msg="Button fields should not have any initialization"):
            _ = at.session_state["test_key"]

    @staticmethod
    def _get_field(at: AppTest):
        return at.button("test_key")

    def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
        self.assertFalse(self._get_field(at=at).value)

    def _run_field_post_interaction_checks(self, at: AppTest):
        self._get_field(at=at).click()
        at.run()
        self.assertTrue(self._get_field(at=at).value)
