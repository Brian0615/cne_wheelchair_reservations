from unittest import TestCase

from streamlit.testing.v1 import AppTest

from ui.src.constants import CNEDates


class TestUtils(TestCase):

    def test_get_date_input(self):

        def run_get_date_input():
            from ui.src.utils import get_date_input

            get_date_input(label="Date", key_prefix="test")

        # test default date
        at = AppTest.from_function(run_get_date_input).run()
        self.assertEqual(at.date_input("test_date").value, CNEDates.get_default_date())
        self.assertEqual(at.date_input("test_date").min, CNEDates.get_cne_date_list()[0])
        self.assertEqual(at.date_input("test_date").max, CNEDates.get_cne_date_list()[-1])

        # test date after change
        new_date = CNEDates.get_cne_date_list()[-1]
        at.date_input("test_date").set_value(new_date)
        at.run()
        self.assertEqual(at.date_input("test_date").value, new_date)
