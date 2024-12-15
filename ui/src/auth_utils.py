import os
from typing import Optional

import streamlit as st
import streamlit_authenticator as st_auth
import yaml


def load_auth_config():
    try:
        with open(os.environ["AUTH_CONFIG_PATH"], "r") as config_file:
            return yaml.safe_load(config_file)
    except KeyError:
        st.error("**Authentication Error**: Authentication config filepath not provided.")
    except FileNotFoundError:
        st.error("**Authentication Error**: Authentication config file not found.")


def initialize_authenticator() -> st_auth.Authenticate:
    if "authenticator" in st.session_state:
        return st.session_state["authenticator"]

    auth_config = load_auth_config()
    authenticator = st_auth.Authenticate(
        credentials=os.environ["AUTH_CONFIG_PATH"],
        cookie_name=auth_config['cookie']['name'],
        cookie_key=auth_config['cookie']['key'],
        cookie_expiry_days=auth_config['cookie']['expiry_days'],
        auto_hash=True,
    )
    st.session_state["authenticator"] = authenticator
    return authenticator


def login(rendered: bool = False):
    if os.getenv("DEV_MODE", default=False) in [True, 'True', 'true']:
        with st.expander("Session State"):
            st.write(st.session_state)
    authenticator = initialize_authenticator()
    try:
        authenticator.login(
            location="main" if rendered else "unrendered",
            max_login_attempts=5,
        )
    except Exception as e:
        st.error(e)

    if st.session_state["authentication_status"] is True:
        st.sidebar.write(f"Welcome, **{st.session_state['username']}**!")
        authenticator.logout(button_name=":material/logout: Logout", location="sidebar")
        if rendered:  # only on login page, rerun to redirect to home page
            st.rerun()
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
        st.stop()
    elif st.session_state["authentication_status"] is None:
        if not rendered:  # redirect to login page if not on login page
            st.switch_page("ui_pages/login.py")
        else:
            st.warning('Please enter your username and password')
        st.stop()


def initialize_page(page_header: Optional[str] = None):
    st.set_page_config(layout="wide")
    login()
    if page_header:
        st.header(page_header)
