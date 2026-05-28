from typing import Optional
from unittest import TestCase
from unittest.mock import MagicMock, patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from ui.auth.local_authenticator import LocalAuthenticator


class WorkflowTestCase(TestCase):
    """Base class for workflow tests covering end-to-end user journeys."""

    page_path: Optional[str] = None

    def _init_app_test(self, roles: Optional[list] = None, auth_groups: Optional[list] = None) -> AppTest:
        st.cache_data.clear()
        at = AppTest.from_file(self.page_path, default_timeout=10)
        at.session_state["authentication_status"] = True
        at.session_state["username"] = "test_user"
        if roles is not None:
            at.session_state["roles"] = roles
        if auth_groups is not None:
            at.session_state["auth_groups"] = auth_groups
        return at

    def _run(
            self,
            mock_responses,
            at: Optional[AppTest] = None,
            allow_errors: bool = False,
            roles: Optional[list] = None,
            auth_groups: Optional[list] = None,
    ) -> AppTest:
        if at is None:
            at = self._init_app_test(roles=roles, auth_groups=auth_groups)
        with patch("requests.get", side_effect=mock_responses.get), \
                patch("requests.post", side_effect=mock_responses.post), \
                patch("requests.put", side_effect=mock_responses.put), \
                patch.multiple(
                    LocalAuthenticator,
                    login=MagicMock(return_value=True),
                    _initialize_authenticator=MagicMock(),
                    get_current_user=MagicMock(return_value="test_user"),
                ):
            at.run()
        if not allow_errors:
            self.assertEqual(0, len(at.error), f"Unexpected errors: {[e.value for e in at.error]}")
        return at

    def test_unauthenticated_redirects_to_login(self):
        if self.page_path is None:
            self.skipTest("Base class — no page_path set")
        with patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            st.switch_page = MagicMock()
            at = AppTest.from_file(self.page_path)
            at.run()
            st.switch_page.assert_called_once_with("ui/ui_pages/login.py")
