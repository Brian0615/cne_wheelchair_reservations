from datetime import datetime, time, timedelta
from unittest import TestCase

from streamlit.testing.v1 import AppTest

from ui.src.utils import get_default_timezone


class TestTimeField(TestCase):
    """Test the Time Field"""

    def test_initialize_field(self):
        """Test initializing a new Time Field"""

        # pylint: disable=import-outside-toplevel,reimported,redefined-outer-name
        def run_initialize_field():
            from datetime import time

            from ui.forms.form_fields.time_field import TimeField

            field = TimeField(key="test_key", label="Test Label", default_value=time(hour=15, minute=30))
            field.initialize_field()

        at = AppTest.from_function(run_initialize_field).run()
        self.assertEqual(at.session_state["test_key"], time(hour=15, minute=30))

    def test_render(self):
        """Test rendering a Time Field"""

        # pylint: disable=import-outside-toplevel
        def run_render(is_disabled: bool):
            from ui.forms.form_fields.time_field import TimeField

            field = TimeField(key="test_key", label="Test Label")
            field.initialize_field()
            field.render(disabled=is_disabled)

        for disabled in [True, False]:
            with self.subTest(f"Render with disabled={disabled}"):
                at = AppTest.from_function(run_render, kwargs={"is_disabled": disabled})
                at.run()

                self.assertEqual(at.time_input("test_key").disabled, disabled)
                self.assertEqual(at.time_input("test_key").label, "Test Label")
                self.assertLessEqual(
                    (
                        datetime.now(tz=get_default_timezone()).replace(tzinfo=None)
                        - datetime.combine(
                            datetime.now(tz=get_default_timezone()).date(),
                            at.time_input("test_key").value
                        )
                    ),
                    timedelta(minutes=1)
                )
                self.assertEqual(at.time_input("test_key").step, timedelta(minutes=30).total_seconds())

                if not disabled:
                    at.time_input("test_key").set_value(time(hour=11, minute=30))
                    at.run()
                    self.assertEqual(at.time_input("test_key").value, time(hour=11, minute=30))
