import unittest
from unittest.mock import MagicMock, Mock, patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from ui.auth.local_authenticator import LocalAuthenticator


class TestMain(unittest.TestCase):
    """Test the main.py file."""

    __APP_PATH = "ui/main.py"

    @staticmethod
    def test_main_unauthenticated():
        """Test the main page when the user is unauthenticated."""

        # mock the navigation method so we can check the pages
        st.navigation = Mock()

        with patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            # test for when user has never authenticated yet
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.run()
            page_list = st.navigation.call_args.kwargs["pages"]
            page_list = sum(page_list.values(), [])
            assert len(page_list) == 1 and page_list[0].title == "Login", \
                "Only the login page should be available when unauthenticated."

            # test for after user logs out
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = False
            at.run()

            page_list = st.navigation.call_args.kwargs["pages"]
            page_list = sum(page_list.values(), [])
            assert len(page_list) == 1 and page_list[0].title == "Login", \
                "Only the login page should be available when unauthenticated."

    @staticmethod
    def test_main_authenticated():
        """Test the main page when the user is authenticated."""

        # mock the navigation method so we can check the pages
        st.navigation = Mock()

        with patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = True
            at.session_state["roles"] = []
            at.run()
            page_list = st.navigation.call_args.kwargs["pages"]
            page_list = sum(page_list.values(), [])
            assert len(page_list) >= 1, "At least one page should be available when authenticated."
            assert not any(page.title == "Login" for page in page_list), \
                "The login page should not be available when authenticated."
