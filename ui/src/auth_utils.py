import os
from typing import Optional

import streamlit as st

from ui.auth.local_authenticator import LocalAuthenticator


def initialize_page(page_header: Optional[str] = None, render_login: bool = False):
    """Initialize a Streamlit page with login and optional header."""

    st.set_page_config(layout="centered" if render_login else "wide")

    # developer mode details
    if os.getenv("DEV_MODE", default="False").lower() == "true":
        with st.expander("Developer Details", expanded=False):
            tabs = st.tabs(["Session State", "Headers", "Query Params", "Cookies"])
            tabs[0].write(st.session_state)
            tabs[1].write(st.context.headers)
            tabs[2].write(st.query_params)
            tabs[3].write(st.context.cookies)

    # authentication setup
    match os.getenv("AUTH_METHOD", default="local"):
        case "local":
            authenticator = LocalAuthenticator()
        case _:
            raise ValueError("Invalid authentication method. Supported methods: local, cognito")

    # handle authentication
    if not authenticator.login(rendered=render_login):
        if render_login:
            st.stop()
        st.switch_page("ui/ui_pages/login.py")

    if render_login:
        st.rerun()
    authenticator.render_logout()
    if page_header:
        st.header(page_header)
