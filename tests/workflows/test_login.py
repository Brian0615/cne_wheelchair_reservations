import os

import streamlit as st
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

from tests.workflows.base import WorkflowTestCase
from ui.auth.cognito_authenticator import CognitoAuthenticator
from ui.auth.local_authenticator import LocalAuthenticator


class LoginWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Login page."""

    page_path = "ui/ui_pages/login.py"

    _AUTH_CASES = [
        (LocalAuthenticator, "local"),
        (CognitoAuthenticator, "cognito"),
    ]

    def test_unauthenticated_redirects_to_login(self):
        # Login page calls st.rerun() (not st.switch_page) for unauthenticated users,
        # so the base redirect test does not apply here.
        pass

    def test_unauthenticated_does_not_crash(self):
        """Unauthenticated access to the login page calls st.stop() cleanly, without errors."""
        for authenticator_class, auth_method in self._AUTH_CASES:
            with self.subTest(auth_method=auth_method):
                with patch.dict(os.environ, {"AUTH_METHOD": auth_method}), \
                        patch.multiple(
                            authenticator_class,
                            _initialize_authenticator=MagicMock(),
                            login=MagicMock(return_value=False),
                        ):
                    at = AppTest.from_file(self.page_path, default_timeout=5)
                    at.run()
                # st.stop() raises internally but is caught by Streamlit; no unhandled Python error
                self.assertEqual(0, len(at.error),
                                 f"[{auth_method}] No error widgets should be rendered on the login page")

    def test_already_logged_in_shows_welcome_message(self):
        """User visiting the login page while already authenticated sees the 'already logged in' message with their
        username and the logout button is rendered in the sidebar.
        """
        for authenticator_class, auth_method in self._AUTH_CASES:
            with self.subTest(auth_method=auth_method):
                mock_render_logout = MagicMock()
                with patch.dict(os.environ, {"AUTH_METHOD": auth_method}), \
                        patch.multiple(
                            authenticator_class,
                            _initialize_authenticator=MagicMock(),
                            login=MagicMock(return_value=True),
                            get_current_user=MagicMock(return_value="test_user"),
                            is_authenticated=MagicMock(return_value=True),
                            render_logout=mock_render_logout,
                        ), patch.object(st, "rerun", MagicMock()):
                    at = AppTest.from_file(self.page_path, default_timeout=5)
                    at.session_state["authentication_status"] = True
                    at.session_state["username"] = "test_user"
                    at.run()
                self.assertEqual(0, len(at.error), f"[{auth_method}] No errors should be rendered")
                self.assertEqual(1, len(at.success), f"[{auth_method}] A success message should be displayed")
                self.assertIn("test_user", at.success[0].value,
                              f"[{auth_method}] Username should appear in the message")
                self.assertIn("already logged in", at.success[0].value,
                              f"[{auth_method}] 'Already logged in' text should appear in the message")
                mock_render_logout.assert_called_once_with(), f"[{auth_method}] render_logout should be called to display the logout button"

    def test_logout_clears_authentication_state(self):
        """After logout, the session is cleared and the login page no longer shows the already-logged-in message.

        The logout flow calls _on_logout which invokes _clear_session_state, removing authentication_status
        and username from session state. This test simulates that state change and verifies the page
        reverts to the unauthenticated (login form) state with no errors.
        """
        for authenticator_class, auth_method in self._AUTH_CASES:
            with self.subTest(auth_method=auth_method):
                # Phase 1: render the page in an authenticated state
                with patch.dict(os.environ, {"AUTH_METHOD": auth_method}), \
                        patch.multiple(
                            authenticator_class,
                            _initialize_authenticator=MagicMock(),
                            login=MagicMock(return_value=True),
                            get_current_user=MagicMock(return_value="test_user"),
                            is_authenticated=MagicMock(return_value=True),
                            render_logout=MagicMock(),
                        ), patch.object(st, "rerun", MagicMock()):
                    at = AppTest.from_file(self.page_path, default_timeout=5)
                    at.session_state["authentication_status"] = True
                    at.session_state["username"] = "test_user"
                    at.run()
                self.assertEqual(1, len(at.success),
                                 f"[{auth_method}] Should see 'already logged in' message before logout")

                # Phase 2: simulate logout — mirrors what _on_logout/_clear_session_state does
                del at.session_state["authentication_status"]
                del at.session_state["username"]

                with patch.dict(os.environ, {"AUTH_METHOD": auth_method}), \
                        patch.multiple(
                            authenticator_class,
                            _initialize_authenticator=MagicMock(),
                            login=MagicMock(return_value=False),
                        ):
                    at.run()
                self.assertEqual(0, len(at.success), f"[{auth_method}] No success message should be shown after logout")
                self.assertEqual(0, len(at.error), f"[{auth_method}] No errors should be shown after logout")

    def test_successful_login_shows_welcome_message(self):
        """Authenticated user on the login page sees a success message containing their username.

        st.rerun() is patched as a no-op to prevent an infinite rerun loop; without the patch,
        initialize_page() would trigger a rerun on every successful login check.
        """
        for authenticator_class, auth_method in self._AUTH_CASES:
            with self.subTest(auth_method=auth_method):
                with patch.dict(os.environ, {"AUTH_METHOD": auth_method}), \
                        patch.multiple(
                            authenticator_class,
                            _initialize_authenticator=MagicMock(),
                            login=MagicMock(return_value=True),
                            get_current_user=MagicMock(return_value="test_user"),
                            is_authenticated=MagicMock(return_value=True),
                            render_logout=MagicMock(),
                        ), patch.object(st, "rerun", MagicMock()):
                    at = AppTest.from_file(self.page_path, default_timeout=5)
                    at.session_state["authentication_status"] = True
                    at.session_state["username"] = "test_user"
                    at.run()
                self.assertEqual(0, len(at.error),
                                 f"[{auth_method}] No error widgets should be rendered on successful login")
                self.assertEqual(1, len(at.success),
                                 f"[{auth_method}] A success message should be displayed after login")
                self.assertIn("test_user", at.success[0].value)
