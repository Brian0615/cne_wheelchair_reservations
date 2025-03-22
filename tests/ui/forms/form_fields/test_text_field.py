from streamlit.testing.v1 import AppTest

from tests.base_tests import BaseTestCases
from ui.forms.form_fields.text_field import TextField


class TestTextField(BaseTestCases.BaseFormFieldTest):
    """Test the Text Field"""

    def setUp(self):
        self.field_class = TextField

    def test_initialize_field(self):
        """Test initializing a new Text Field"""

        for default in [None, "test_input"]:
            with self.subTest(msg=f"Default value={default}"):
                super()._test_initialize_field_with_kwargs(
                    kwargs_dict={"default_value": default},
                    expected_init_value=default,
                )

    @staticmethod
    def _get_field(at: AppTest):
        return at.text_input("test_key")

    def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
        self.assertEqual(self._get_field(at=at).value, None)

    def _run_field_post_interaction_checks(self, at: AppTest):
        self._get_field(at=at).input("abcdef")
        at.run()
        self.assertEqual(self._get_field(at=at).value, "abcdef")
