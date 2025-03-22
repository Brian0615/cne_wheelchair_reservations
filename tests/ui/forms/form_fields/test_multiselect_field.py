from streamlit.testing.v1 import AppTest

from tests.base_tests import BaseTestCases
from ui.forms.form_fields import MultiSelectField


class TestMultiSelectField(BaseTestCases.BaseFormFieldTest):
    """Test the Multiselect Field"""

    def setUp(self):
        self.field_class = MultiSelectField
        self.expected_init_value = []

    def test_initialize_field(self):
        """Test initializing a new Multiselect Field"""

        for default in [[], ["a"], ["a", "b"]]:
            with self.subTest(msg=f"Default value={default}"):
                super()._test_initialize_field_with_kwargs(
                    kwargs_dict={"options": ["a", "b", "c"], "default_value": default},
                    expected_init_value=default
                )

    @staticmethod
    def _get_field(at: AppTest):
        return at.multiselect("test_key")

    def test_render(self):
        """Test rendering a Multiselect field"""

        super()._test_render_with_kwargs(kwargs_dict={"options": ["a", "b"]})

    def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
        self.assertEqual(self._get_field(at=at).options, ["a", "b"])
        self.assertEqual(self._get_field(at=at).value, [])

    def _run_field_post_interaction_checks(self, at: AppTest):
        self._get_field(at=at).select("a")
        at.run()
        self.assertEqual(self._get_field(at=at).value, ["a"])
        self._get_field(at=at).select("b")
        at.run()
        self.assertEqual(self._get_field(at=at).value, ["a", "b"])
        self._get_field(at=at).unselect("a")
        at.run()
        self.assertEqual(self._get_field(at=at).value, ["b"])
        self._get_field(at=at).unselect("b")
        at.run()
        self.assertEqual(self._get_field(at=at).value, [])
