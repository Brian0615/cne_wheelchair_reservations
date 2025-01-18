import streamlit as st

# determine pages to display depending on authentication status
if st.session_state.get("authentication_status", None) is True:  # already authenticated
    # default pages
    pages = {
        "Home": [
            st.Page("ui_pages/home.py", title="Home", icon=":material/home:", default=True)
        ],
        "Rentals": [
            st.Page("ui_pages/view_rentals.py", title="View Rentals", icon=":material/manage_search:"),
        ],
        "Reservations": [
            st.Page("ui_pages/view_reservations.py", title="View Reservations", icon=":material/manage_search:"),
        ],
        "Inventory": [
            st.Page("ui_pages/view_inventory.py", title="View Inventory", icon=":material/manage_search:"),
        ],
    }

    # add privileged pages
    if "admin" in st.session_state.get("roles", []):
        pages["Rentals"].append(
            st.Page("ui_pages/manage_rental.py", title="Manage Rental", icon=":material/settings:")
        )
        pages["Reservations"].append(
            st.Page("ui_pages/manage_reservations.py", title="Manage Reservations", icon=":material/settings:")
        )
        pages["Inventory"].append(
            st.Page("ui_pages/manage_inventory.py", title="Manage Inventory", icon=":material/settings:")
        )
    if "editor" in st.session_state.get("roles", []):
        pages["Rentals"] += [
            st.Page("ui_pages/new_rental.py", title="New Rental", icon=":material/add_circle:"),
            st.Page("ui_pages/complete_rental.py", title="Complete Rental", icon=":material/check_circle:"),
        ]
        pages["Reservations"].append(
            st.Page("ui_pages/new_reservation.py", title="New Reservation", icon=":material/add_circle:")
        )

else:  # not authenticated
    pages = {
        "Authentication": [
            st.Page("ui_pages/login.py", title="Login", icon=":material/login:", default=True)
        ]
    }

navigator = st.navigation(pages=pages)
navigator.run()
