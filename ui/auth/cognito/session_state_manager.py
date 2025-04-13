from typing import Any, Optional, Tuple

import streamlit as st
from pydantic import ValidationError

from ui.auth.cognito.credentials import Credentials


class CognitoAuthSessionStateManager:
    """Saves and loads authorization credentials to streamlit session state."""

    def __init__(self) -> None:

        self._init_state("auth_id_token")
        self._init_state("auth_access_token")
        self._init_state("auth_refresh_token")
        self._init_state("auth_expires_in")
        self._init_state("auth_token_type")
        self._init_state("auth_state")
        self._init_state("auth_username")
        self._init_state("auth_reset_password_session")
        self._init_state("auth_reset_password_username")
        self._init_state("auth_reset_password_password")

    @staticmethod
    def _init_state(name, default_value: Any = ""):
        if not name in st.session_state:
            st.session_state[name] = default_value

    @staticmethod
    def set_credentials(credentials: Credentials) -> None:
        """Saves the credentials to streamlit session state."""
        st.session_state["auth_id_token"] = credentials.id_token
        st.session_state["auth_access_token"] = credentials.access_token
        st.session_state["auth_refresh_token"] = credentials.refresh_token
        st.session_state["auth_expires_in"] = credentials.expires_in
        st.session_state["auth_token_type"] = credentials.token_type

    @staticmethod
    def reset_credentials() -> None:
        """Clears the credentials from streamlit session state."""
        st.session_state["auth_id_token"] = ""
        st.session_state["auth_access_token"] = ""
        st.session_state["auth_refresh_token"] = ""
        st.session_state["auth_expires_in"] = 0
        st.session_state["auth_token_type"] = ""

    @staticmethod
    def load_credentials() -> Optional[Credentials]:
        """Loads the credentials from streamlit session state.

        Returns None if no credentials were found."""
        try:
            return Credentials(
                id_token=st.session_state["auth_id_token"],
                access_token=st.session_state["auth_access_token"],
                refresh_token=st.session_state["auth_refresh_token"],
                expires_in=st.session_state["auth_expires_in"],
                token_type=st.session_state["auth_token_type"],
            )
        except ValidationError:
            return None

    @staticmethod
    def set_logged_in(username: Optional[str], email: Optional[str]) -> None:
        """Sets the logged in flag and the username in streamlit session state."""
        st.session_state["auth_state"] = "logged_in"
        st.session_state["auth_username"] = username
        st.session_state["auth_email"] = email

    @staticmethod
    def set_logged_out() -> None:
        """Clears the logged in flag from streamlit session state."""
        st.session_state["auth_state"] = "logged_out"
        st.session_state["auth_username"] = ""

    @staticmethod
    def is_logged_in() -> bool:
        """Returns if the user is currently logged in as of the streamlit session state."""
        return st.session_state["auth_state"] == "logged_in"

    @staticmethod
    def get_username() -> Optional[str]:
        """Returns the username saved in streamlit session state."""
        return st.session_state.get("auth_username") or None

    @staticmethod
    def get_email() -> Optional[str]:
        """Returns the email saved in streamlit session state."""
        return st.session_state.get("auth_email") or None

    @staticmethod
    def set_reset_password_session(
            reset_password_username: str,
            reset_password_password: str,
            reset_password_session: str = "reset_password",
    ) -> None:
        """Sets the password reset session to streamlit session state."""
        st.session_state["auth_reset_password_session"] = reset_password_session
        st.session_state["auth_reset_password_username"] = reset_password_username
        st.session_state["auth_reset_password_password"] = reset_password_password

    @staticmethod
    def clear_reset_password_session() -> None:
        """Clears the password reset session from streamlit session state/"""
        st.session_state["auth_reset_password_session"] = ""
        st.session_state["auth_reset_password_username"] = ""
        st.session_state["auth_reset_password_password"] = ""

    @staticmethod
    def is_reset_password_session() -> bool:
        """Returns if password reset session is set in streamlit session state."""
        return bool(st.session_state["auth_reset_password_session"])

    @staticmethod
    def reset_password_credentials() -> Tuple[Optional[str], Optional[str]]:
        """Returns the password reset username and password saved in streamlit session state."""
        username = st.session_state["auth_reset_password_username"] or None
        password = st.session_state["auth_reset_password_password"] or None
        return username, password
