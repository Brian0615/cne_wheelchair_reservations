from unittest.mock import MagicMock, patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from tests.workflows.base import WorkflowTestCase
from ui.auth.local_authenticator import LocalAuthenticator


class LoginWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Login page.

    Note: initialize_page(render_login=True) unconditionally calls st.rerun() after login
    succeeds, making the authenticated path untestable via AppTest (infinite rerun loop).
    Tests here are limited to the unauthenticated state.
    """

    page_path = "ui/ui_pages/login.py"

    def test_unauthenticated_redirects_to_login(self):
        # Login page calls st.rerun() (not st.switch_page) for unauthenticated users,
        # so the base redirect test does not apply here.
        pass

    def test_unauthenticated_does_not_crash(self):
        """Unauthenticated access to the login page calls st.stop() cleanly, without errors."""
        with patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            at = AppTest.from_file(self.page_path, default_timeout=5)
            at.run()
        # st.stop() raises internally but is caught by Streamlit; no unhandled Python error
        self.assertEqual(0, len(at.error), "No error widgets should be rendered on the login page")
