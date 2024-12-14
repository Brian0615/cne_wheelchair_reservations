import streamlit as st

from ui.src.auth_utils import login

# check if already logged in
if st.session_state.get("authentication_status", None) is True:
    st.success(
        f"""
        You are already logged in as **{st.session_state['username']}**. Use the sidebar to navigate to other pages.
        
        **Not {st.session_state['username']}?** Use the Logout button in the sidebar.
        """
    )

login(rendered=True)
