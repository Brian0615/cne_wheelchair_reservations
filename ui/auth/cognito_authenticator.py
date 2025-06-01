import os
from typing import Any, List

import streamlit as st

from common.utils import read_secret
from ui.auth.base_authenticator import BaseAuthenticator
from ui.auth.cognito.authenticator import CognitoAuthenticator as CognitoAuth


class CognitoAuthenticator(BaseAuthenticator):
    """
    A class for handling authentication using AWS Cognito in a Streamlit application.
    """

    def _initialize_authenticator(self) -> Any:
        """
        Initializes the authenticator. This method is not implemented for Cognito.

        Returns:
            Any: Always returns None.
        """
        return CognitoAuth(
            pool_id=read_secret(os.environ["AWS_COGNITO_USER_POOL_ID"]),
            app_client_id=read_secret(os.environ["AWS_COGNITO_CLIENT_ID"]),
            app_client_secret=read_secret(os.environ["AWS_COGNITO_CLIENT_SECRET"]),
            use_cookies=False
        )

    def get_current_user(self) -> str:
        """Retrieves the username of the currently authenticated user."""
        return self.authenticator.get_username()

    def get_current_user_groups(self) -> List[str]:
        """
        Retrieves the groups of the currently authenticated user.

        Returns:
            List[str]: A list of groups the user belongs to.
        """
        return self.authenticator.get_user_groups()

    def is_admin_user(self) -> bool:
        """
        Checks if the current user is an admin.

        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        return "cne-admin" in self.get_current_user_groups()

    def is_editor_user(self) -> bool:
        """
        Checks if the current user is an editor.

        Returns:
            bool: True if the user is an editor, False otherwise.
        """
        return self.is_admin_user() or "cne-editor" in self.get_current_user_groups()

    def is_authenticated(self) -> bool:
        """ Checks if the user is authenticated."""
        return self.authenticator.is_logged_in()

    # pylint: disable=unused-argument,fixme
    def login(self, rendered: bool = False) -> bool:
        """
        Handles the login process by validating the user through ALB headers.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        return self.authenticator.login()

    def _on_logout(self):
        self._clear_session_state(
            keep_keys={
                "auth_id_token",
                "auth_access_token",
                "auth_refresh_token",
                "auth_expires_in",
                "auth_token_type",
                "auth_reset_password_session",
            }
        )
        self.authenticator.logout()

    def render_logout(self):
        """
        Renders a logout button in the Streamlit sidebar.
        """
        st.sidebar.button(
            ":material/logout: Logout",
            on_click=self._on_logout,
            key="logout_button",
        )
