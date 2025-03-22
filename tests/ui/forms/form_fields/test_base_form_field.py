from streamlit.testing.v1 import AppTest

from tests.base_tests import BaseTestCases
from ui.forms.form_fields.base_form_field import BaseFormField


# pylint: disable=import-outside-toplevel,redefined-outer-name,reimported
class TestBaseFormField(BaseTestCases.BaseFormFieldTest):
    """Base class for testing a Form Field"""

    def setUp(self):
        self.field_class = BaseFormField
        self.expected_init_value = None

    def test_previously_initialized_field(self):
        """Test initializing a previously initialized field"""
        def run_previously_initialized_field():
            import streamlit as st

            from ui.forms.form_fields.base_form_field import BaseFormField

            st.session_state["test_key"] = "Test Value"
            field = BaseFormField(key="test_key", label="Test Label")
            field.initialize_field()

        at = AppTest.from_function(run_previously_initialized_field).run()
        self.assertEqual(at.session_state["test_key"], "Test Value")

    def test_render(self):
        """Test rendering a Form Field"""

        # note: this error would not be explicitly raised because it is raised inside the AppTest
        at = AppTest.from_function(script=self._run_field, args=(self.field_class, ), kwargs={"render": True}).run()
        self.assertEqual(at.exception[0].proto.type, "NotImplementedError")

    def test_clear_field(self):
        """Clear field cannot be tested as it requires render to be implemented"""

    @staticmethod
    def _get_field(at: AppTest):
        """Not implemented as nothing is actually rendered in the base class"""

    def _run_field_post_render_checks(self, at: AppTest, disabled: bool):
        pass

    def _run_field_post_interaction_checks(self, at: AppTest):
        pass
