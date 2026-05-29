from datetime import time

from streamlit.testing.v1 import AppTest

from tests.unit.base_tests import BaseTestCases
from ui.forms.form_fields.time_field import TimeField


class TestTimeField(BaseTestCases.BaseFormFieldTest):
    """Test the Time Field"""

    def setUp(self):
        self.field_class = TimeField
        self.expected_init_value = None

    def test_initialize_field(self):
        """Test initializing a new Time Field"""

        super()._test_initialize_field_with_kwargs(
            kwargs_dict={"default_value": time(hour=15, minute=30)},
            expected_init_value=time(hour=15, minute=30),
        )

    @staticmethod
    def _get_field(at: AppTest):
        return at.time_input("test_key")

    def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
        self.assertIsNone(self._get_field(at=at).value)

    def _run_field_post_interaction_checks(self, at: AppTest):
        self._get_field(at=at).set_value(time(hour=11, minute=30))
        at.run()
        self.assertEqual(self._get_field(at=at).value, time(hour=11, minute=30))
