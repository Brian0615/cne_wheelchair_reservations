from streamlit.testing.v1 import AppTest

from tests.unit.base_tests import BaseTestCases
from ui.forms.form_fields.selectbox_field import SelectboxField


# pylint: disable=import-outside-toplevel,duplicate-code
class TestSelectboxField(BaseTestCases.BaseFormFieldTest):
    """Test the Selectbox Field"""

    def setUp(self):
        self.field_class = SelectboxField
        self.expected_init_value = None

    def test_initialize_field(self):
        """Test initializing a new Selectbox Field"""

        for default in [None, "b"]:
            with self.subTest(msg=f"Default value={default}"):
                super()._test_initialize_field_with_kwargs(
                    kwargs_dict={"options": ["a", "b", "c"], "default_value": default},
                    expected_init_value=default,
                )

    @staticmethod
    def _get_field(at: AppTest):
        return at.selectbox("test_key")

    def test_render(self):
        """Test rendering a Selectbox field"""
        super()._test_render_with_kwargs(kwargs_dict={"options": ["a", "b"]})

    def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
        self.assertEqual(self._get_field(at=at).options, ["a", "b"])
        self.assertEqual(self._get_field(at=at).value, None)

    def _run_field_post_interaction_checks(self, at: AppTest):
        self._get_field(at=at).select("a")
        at.run()
        self.assertEqual(self._get_field(at=at).value, "a")
        self._get_field(at=at).select("b")
        at.run()
        self.assertEqual(self._get_field(at=at).value, "b")
