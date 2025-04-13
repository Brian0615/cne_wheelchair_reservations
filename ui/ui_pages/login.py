import streamlit as st

from ui.src.auth_utils import initialize_page

authenticator = initialize_page(render_login=True)

# check if already logged in
if authenticator.is_authenticated():
    st.success(
        f"""
        You are already logged in as **{authenticator.get_current_user()}**. Use the sidebar to navigate to other pages.
        
        **Not {authenticator.get_current_user()}?** Use the Logout button in the sidebar.
        """
    )
