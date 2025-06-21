import os
from typing import Optional, Union

import streamlit as st
from streamlit.errors import StreamlitAPIException

from ui.auth.cognito_authenticator import CognitoAuthenticator
from ui.auth.local_authenticator import LocalAuthenticator
from version import APP_VERSION


def get_authenticator() -> Union[LocalAuthenticator, CognitoAuthenticator]:
    """
    Retrieve the appropriate authenticator based on the authentication method.

    Determines the authentication method to use by reading the
    `AUTH_METHOD` environment variable. Supports two methods:
    - "local": Uses the `LocalAuthenticator` for local authentication.
    - "cognito": Uses the `CognitoAuthenticator` for AWS Cognito-based authentication.

    Returns:
        An instance of the appropriate authenticator class.

    Raises:
        ValueError: If the `AUTH_METHOD` environment variable contains an invalid value.
    """
    match os.getenv("AUTH_METHOD", default="local"):
        case "local":
            return LocalAuthenticator()
        case "cognito":
            return CognitoAuthenticator()
        case _:
            raise ValueError("Invalid authentication method. Supported methods: local, cognito")


def initialize_page(page_header: Optional[str] = None, render_login: bool = False):
    """Initialize a Streamlit page with login and optional header."""

    st.set_page_config(
        layout="centered" if render_login else "wide",
        menu_items={
            "About": f"**CNE Wheelchair Reservations** v{APP_VERSION}"
        }
    )

    # developer mode details
    if os.getenv("DEV_MODE", default="False").lower() == "true" and not render_login:
        with st.expander("Developer Details", expanded=False):
            tabs = st.tabs(["Session State", "Headers", "Query Params", "Cookies"])
            tabs[0].write(st.session_state)
            tabs[1].write(st.context.headers)
            tabs[2].write(st.query_params)
            tabs[3].write(st.context.cookies)

    # authentication setup
    authenticator = get_authenticator()

    # handle authentication
    if not authenticator.login(rendered=render_login):
        if render_login:
            st.stop()
        try:
            st.switch_page("ui/ui_pages/login.py")
        except StreamlitAPIException:
            st.rerun()

    if render_login:
        st.rerun()
    st.sidebar.write(f"Welcome, **{authenticator.get_current_user()}**!")
    authenticator.render_logout()
    if page_header:
        st.header(page_header)
    st.sidebar.caption(f"v{APP_VERSION}")

    return authenticator
