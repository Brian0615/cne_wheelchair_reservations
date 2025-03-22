from datetime import timedelta

from streamlit.testing.v1 import AppTest

from tests.base_tests import BaseTestCases
from ui.forms.form_fields.date_field import DateField
from ui.src.constants import CNEDates


# pylint: disable=too-few-public-methods
class TestDateField(BaseTestCases.BaseFormFieldTest):
    """Test the Date Field"""

    def setUp(self):
        self.field_class = DateField
        self.expected_init_value = CNEDates.get_default_date()

    @staticmethod
    def _get_field(at: AppTest):
        return at.date_input("test_key")

    def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
        self.assertEqual(self._get_field(at=at).min, min(CNEDates.get_cne_date_list()))
        self.assertEqual(self._get_field(at=at).max, max(CNEDates.get_cne_date_list()))
        self.assertEqual(self._get_field(at=at).value, CNEDates.get_default_date())

    def _run_field_post_interaction_checks(self, at: AppTest):
        self._get_field(at=at).set_value(CNEDates.get_default_date() + timedelta(days=1))
        at.run()
        self.assertEqual(self._get_field(at=at).value, CNEDates.get_default_date() + timedelta(days=1))
