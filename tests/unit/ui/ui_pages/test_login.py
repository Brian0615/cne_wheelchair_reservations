import streamlit as st
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

from tests.unit.base_tests import BaseTestCases
from ui.auth.local_authenticator import LocalAuthenticator


class TestLogin(BaseTestCases.BaseUIPageTest):
    """Tests for the Login page."""

    def setUp(self):
        self.page_path = "ui/ui_pages/login.py"

    def test_unauthenticated_user(self):
        # The base test expects st.switch_page to be called, but the login page calls
        # st.stop() instead of st.switch_page for unauthenticated users, so skip it.
        pass

    def test_login_page_renders_form_with_submit_button(self):
        """The login form is fully rendered with a submit button for unauthenticated users.

        Guards against the 'Missing Submit Button' bug where the stx.CookieManager
        iframe triggered a mid-render Streamlit rerun that caused the form to be shown
        before its submit button was added.
        """
        def render_login_form(**kwargs):
            if kwargs.get("location") == "main":
                with st.form("Login"):
                    st.text_input("Username")
                    st.text_input("Password")
                    st.form_submit_button("Login")

        mock_inner_auth = MagicMock()
        mock_inner_auth.login.side_effect = render_login_form
        with patch.multiple(
            LocalAuthenticator,
            _initialize_authenticator=MagicMock(return_value=mock_inner_auth),
        ):
            at = AppTest.from_file(self.page_path, default_timeout=5)
            at.run()

        self.assertEqual(0, len(at.exception), "Login page should render without unhandled exceptions")
        self.assertEqual(1, len(at.button), "Login form submit button should be present")
