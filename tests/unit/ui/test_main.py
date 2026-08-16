import unittest
from unittest.mock import MagicMock, patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from ui.auth.local_authenticator import LocalAuthenticator


class TestMain(unittest.TestCase):
    """Test the main.py file."""

    __APP_PATH = "ui/main.py"

    @staticmethod
    def test_main_unauthenticated():
        """Test the main page when the user is unauthenticated."""

        with patch.object(st, "navigation") as mock_navigation, patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            # test for when user has never authenticated yet
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.run()
            page_list = mock_navigation.call_args.kwargs["pages"]
            page_list = sum(page_list.values(), [])
            assert len(page_list) == 1, "Only the login page should be available when unauthenticated."
            assert page_list[0].title == "Login", "Only the login page should be available when unauthenticated."

            # test for after user logs out
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = False
            at.run()

            page_list = mock_navigation.call_args.kwargs["pages"]
            page_list = sum(page_list.values(), [])
            assert len(page_list) == 1, "Only the login page should be available when unauthenticated."
            assert page_list[0].title == "Login", "Only the login page should be available when unauthenticated."

    @staticmethod
    def test_main_authenticated():
        """Test the main page when the user is authenticated."""

        with patch.object(st, "navigation") as mock_navigation, patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = True
            at.session_state["roles"] = []
            at.run()
            page_list = mock_navigation.call_args.kwargs["pages"]
            page_list = sum(page_list.values(), [])
            assert len(page_list) >= 1, "At least one page should be available when authenticated."
            assert not any(page.title == "Login" for page in page_list), \
                "The login page should not be available when authenticated."

    @staticmethod
    def test_main_display_only_user_sees_only_dashboard():
        """A display-only user should see ONLY the Dashboard page."""

        with patch.object(st, "navigation") as mock_navigation, patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = True
            at.session_state["roles"] = ["display"]
            at.run()
            page_list = mock_navigation.call_args.kwargs["pages"]
            page_list = sum(page_list.values(), [])
            assert len(page_list) == 1, "Only the Dashboard page should be available to a display-only user."
            assert page_list[0].title == "Dashboard", \
                "Only the Dashboard page should be available to a display-only user."

    @staticmethod
    def test_main_display_and_editor_user_sees_only_dashboard():
        """A user with both display and editor roles (but not admin) should still see only Dashboard."""

        with patch.object(st, "navigation") as mock_navigation, patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = True
            at.session_state["roles"] = ["display", "editor"]
            at.run()
            page_list = mock_navigation.call_args.kwargs["pages"]
            page_list = sum(page_list.values(), [])
            assert len(page_list) == 1, "Editor pages should not leak in for a display-only user."
            assert page_list[0].title == "Dashboard", "Editor pages should not leak in for a display-only user."

    @staticmethod
    def test_main_admin_user_does_not_see_dashboard():
        """An admin user who is not also in the display group should not see the Dashboard page."""

        with patch.object(st, "navigation") as mock_navigation, patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = True
            at.session_state["roles"] = ["admin"]
            at.run()
            page_list = mock_navigation.call_args.kwargs["pages"]
            page_titles = [page.title for page in sum(page_list.values(), [])]
            assert "Dashboard" not in page_titles, "Admins should not see the Dashboard unless also a display user."
            assert "Home" in page_titles, "Admins should still see their full baseline and privileged page set."
            assert "Manage Inventory" in page_titles, \
                "Admins should still see their full baseline and privileged page set."

    @staticmethod
    def test_main_admin_and_display_user_sees_dashboard_with_full_page_set():
        """A user with both admin and display roles should see the Dashboard plus their full admin page set."""

        with patch.object(st, "navigation") as mock_navigation, patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = True
            at.session_state["roles"] = ["admin", "display"]
            at.run()
            page_list = mock_navigation.call_args.kwargs["pages"]
            page_titles = [page.title for page in sum(page_list.values(), [])]
            assert "Dashboard" in page_titles, "An admin who is also a display user should see the Dashboard."
            assert "Home" in page_titles, "Admins should still see their full baseline and privileged page set."
            assert "Manage Inventory" in page_titles, \
                "Admins should still see their full baseline and privileged page set."

    @staticmethod
    def test_main_editor_user_does_not_see_dashboard():
        """A plain editor user (no admin/display role) should not see the Dashboard page."""

        with patch.object(st, "navigation") as mock_navigation, patch.multiple(
                LocalAuthenticator,
                _initialize_authenticator=MagicMock(),
                login=MagicMock(return_value=False),
        ):
            at = AppTest.from_file(TestMain.__APP_PATH)
            at.session_state["authentication_status"] = True
            at.session_state["roles"] = ["editor"]
            at.run()
            page_list = mock_navigation.call_args.kwargs["pages"]
            page_titles = [page.title for page in sum(page_list.values(), [])]
            assert "Dashboard" not in page_titles, \
                "Plain editor users should not gain Dashboard access."
