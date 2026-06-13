import streamlit as st

from ui.src.auth_utils import get_authenticator

authenticator = get_authenticator()

# On a browser refresh Streamlit starts a fresh session with empty session state, so the
# session must be restored from cookies before deciding which pages to register. Doing it
# here (rather than only inside each page) keeps the user on their current page instead of
# briefly flashing the login page and bouncing them back to Home.
if not authenticator.is_authenticated():
    authenticator.restore_session()

# determine pages to display depending on authentication status
if authenticator.is_authenticated():
    # default pages
    pages = {
        "Home": [
            st.Page("ui_pages/home.py", title="Home", icon=":material/home:", default=True)
        ],
        "Rentals": [
            st.Page("ui_pages/view_rentals.py", title="View Rentals", icon=":material/manage_search:"),
        ],
        "Reservations": [
            st.Page("ui_pages/reservation_availability.py", title="Reservation Availability",
                    icon=":material/event_available:"),
            st.Page("ui_pages/view_reservations.py", title="View Reservations", icon=":material/manage_search:"),
        ],
        "Inventory": [
            st.Page("ui_pages/view_inventory.py", title="View Inventory", icon=":material/manage_search:"),
        ],
    }

    # add privileged pages
    if authenticator.is_admin_user():
        pages["Reservations"] += [
            st.Page("ui_pages/new_reservation.py", title="New Reservation", icon=":material/add_circle:"),
            st.Page("ui_pages/manage_reservation.py", title="Manage Reservation", icon=":material/settings:"),
        ]
        pages["Inventory"].append(
            st.Page("ui_pages/manage_inventory.py", title="Manage Inventory", icon=":material/settings:")
        )
        pages["Assistant"] = [
            st.Page("ui_pages/chatbot.py", title="Chatbot", icon=":material/smart_toy:")
        ]
    if authenticator.is_editor_user():
        pages["Rentals"] += [
            st.Page("ui_pages/new_rental.py", title="New Rental", icon=":material/add_circle:"),
            st.Page("ui_pages/manage_rental.py", title="Manage Rental", icon=":material/settings:"),
            st.Page("ui_pages/complete_rental.py", title="Complete Rental", icon=":material/check_circle:"),
        ]

else:  # not authenticated
    pages = {
        "Authentication": [
            st.Page("ui_pages/login.py", title="Login", icon=":material/login:", default=True)
        ]
    }

navigator = st.navigation(pages=pages)

# Keep the user on their current page across a full-page browser refresh, but only while
# they stay logged in. st.navigation tracks the active page in the URL path, yet on a fresh
# session it can fall back to the default (Home) page before the page is resolved. The
# active page is therefore mirrored into a query param (query params are available
# synchronously on the first run) and restored once per session if navigation landed
# elsewhere. When the user is not logged in -- including right after logging out -- the
# saved page is cleared so the next login always starts at Home.
_PAGE_QUERY_KEY = "page"
if authenticator.is_authenticated():
    current_page_path = navigator.url_path

    if not st.session_state.get("active_page_restored"):
        st.session_state["active_page_restored"] = True
        saved_page_path = st.query_params.get(_PAGE_QUERY_KEY)
        if saved_page_path and saved_page_path != current_page_path:
            target_page = next(
                (page for section in pages.values() for page in section
                 if page.url_path == saved_page_path),
                None,
            )
            if target_page is not None:
                st.switch_page(target_page)

    if current_page_path:
        st.query_params[_PAGE_QUERY_KEY] = current_page_path
    elif _PAGE_QUERY_KEY in st.query_params:
        del st.query_params[_PAGE_QUERY_KEY]
elif _PAGE_QUERY_KEY in st.query_params:
    # Not logged in (e.g. just logged out): forget any saved page so the next login starts
    # at Home rather than restoring the previous session's page.
    del st.query_params[_PAGE_QUERY_KEY]

navigator.run()
