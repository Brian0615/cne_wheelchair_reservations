import streamlit as st

from ui.src.auth_utils import get_authenticator

authenticator = get_authenticator()

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
navigator.run()
