from unittest import TestCase

from streamlit.testing.v1 import AppTest


# pylint: disable=import-outside-toplevel
class TestNewReservationForm(TestCase):
    """Tests for NewReservationForm"""

    @staticmethod
    def _run_form(render: bool, clear: bool = False):
        from ui.forms.new_reservation_form import NewReservationForm

        form = NewReservationForm(key_prefix="test_form")
        form.initialize_form()
        if render:
            form.render_form()
        if clear:
            form.clear_form()

    def test_initialize_form(self):
        """Checkbox field does not write to session state on initialize (CheckboxField._initialize is noop)"""
        at = AppTest.from_function(self._run_form, args=(False,)).run()
        with self.assertRaises(KeyError):
            _ = at.session_state["test_form_force_waitlist"]

    def test_render_form_has_waitlist_checkbox(self):
        """Rendered form includes the Add to Waitlist (Override) checkbox, unchecked by default"""
        at = AppTest.from_function(self._run_form, args=(True,)).run()
        self.assertFalse(at.exception)
        self.assertEqual(1, len(at.checkbox), "Exactly one checkbox should be in the rendered form")
        checkbox = at.checkbox("test_form_force_waitlist")
        self.assertEqual("Add to Waitlist (Override)", checkbox.label)
        self.assertFalse(checkbox.value, "Checkbox should be unchecked by default")
        self.assertFalse(checkbox.disabled)

    def test_render_form_force_waitlist_in_result(self):
        """render_form returns force_waitlist key in the result dict"""

        def run_and_capture():
            import streamlit as st
            from ui.forms.new_reservation_form import NewReservationForm

            form = NewReservationForm(key_prefix="test_form")
            form.initialize_form()
            result, _ = form.render_form()
            st.session_state["_test_has_force_waitlist"] = "force_waitlist" in result

        at = AppTest.from_function(run_and_capture).run()
        self.assertTrue(at.session_state["_test_has_force_waitlist"])

    def test_clear_form_removes_force_waitlist(self):
        """clear_form removes the force_waitlist key from session state"""
        at = AppTest.from_function(self._run_form, kwargs={"render": True, "clear": True}).run()
        with self.assertRaises(KeyError):
            _ = at.session_state["test_form_force_waitlist"]

    def test_base_reservation_form_has_no_checkbox(self):
        """Base ReservationForm does not render the waitlist override checkbox"""

        def run_base_form():
            from ui.forms.reservation_form import ReservationForm

            form = ReservationForm(key_prefix="test_form")
            form.initialize_form()
            form.render_form()

        at = AppTest.from_function(run_base_form).run()
        self.assertFalse(at.exception)
        self.assertEqual(0, len(at.checkbox), "Base ReservationForm should not render any checkboxes")
