import streamlit as st

pages = st.navigation(
    {
        "Home": [
            st.Page("ui_pages/home.py", title="Home", icon=":material/home:", default=True),
        ],
        "Rentals": [
            st.Page("ui_pages/view_rentals.py", title="View Rentals", icon=":material/manage_search:"),
            st.Page("ui_pages/manage_rental.py", title="Manage Rental", icon=":material/settings:"),
            st.Page("ui_pages/new_rental.py", title="New Rental", icon=":material/add_circle:"),
        ],
        "Reservations": [
            st.Page("ui_pages/view_reservations.py", title="View Reservations", icon=":material/manage_search:"),
            st.Page("ui_pages/manage_reservations.py", title="Manage Reservations", icon=":material/settings:"),
            st.Page("ui_pages/new_reservation.py", title="New Reservation", icon=":material/add_circle:"),
        ],
        "Inventory": [
            st.Page("ui_pages/view_inventory.py", title="View Inventory", icon=":material/manage_search:"),
            st.Page("ui_pages/manage_inventory.py", title="Manage Inventory", icon=":material/settings:"),
        ],
    }
)
pages.run()
