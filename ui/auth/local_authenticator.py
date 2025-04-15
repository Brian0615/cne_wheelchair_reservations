import os

import streamlit as st
import streamlit_authenticator as st_auth
import yaml

from ui.auth.base_authenticator import BaseAuthenticator


class LocalAuthenticator(BaseAuthenticator):
    """Authenticator for local authentication using Streamlit Authenticator"""

    def _initialize_authenticator(self) -> st_auth.Authenticate:
        """Initialize the Streamlit authenticator"""

        auth_config = self._load_config()
        authenticator = st_auth.Authenticate(
            credentials=os.environ["AUTH_CONFIG_PATH"],
            cookie_name=auth_config['cookie']['name'],
            cookie_key=auth_config['cookie']['key'],
            cookie_expiry_days=auth_config['cookie']['expiry_days'],
            auto_hash=True,
        )
        return authenticator

    def _load_config(self):
        """Load authentication configuration from file"""
        try:
            with open(os.environ["AUTH_CONFIG_PATH"], "r", encoding="utf-8") as config_file:
                return yaml.safe_load(config_file)
        except (KeyError, FileNotFoundError) as e:
            st.error(f"**Authentication Error**: {str(e)}")
            raise

    def get_current_user(self) -> str:
        return st.session_state["username"]

    def is_authenticated(self) -> bool:
        return st.session_state.get("authentication_status", False) is True

    def login(self, rendered: bool = False) -> bool:
        """Handle user login"""
        try:
            self.authenticator.login(
                location="main" if rendered else "unrendered",
                max_login_attempts=5,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            st.error(e)
            return False

        status = st.session_state.get("authentication_status")
        if status is True:
            return True
        if status is False:
            st.error("Username/password is incorrect")
        else:
            st.info("Please enter your username and password")
        return False

    def render_logout(self):
        """Render logout button"""
        self.authenticator.logout(
            button_name=":material/logout: Logout",
            location="sidebar",
            callback=self._on_logout,
        )

    @staticmethod
    def _on_logout(*args, **kwargs):
        """Clear session state on logout"""
        for field in [
            "authentication_status",
            "username",
            "email",
            "roles",
            "name",
        ]:
            del st.session_state[field]
