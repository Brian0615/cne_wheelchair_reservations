import base64
import os
from functools import partial

import streamlit as st
from streamlit_card import card

from common.constants import DeviceType
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_rentals, display_reservations

initialize_page()
data_service = DataService()

cols = st.columns(5, gap="small")
card_info = [
    {
        "asset_path": "assets/new_reservation.png",
        "page_link": "ui_pages/new_reservation.py",
        "key": "card1",
    },
    {
        "asset_path": "assets/start_rental.png",
        "page_link": "ui_pages/new_rental.py",
        "key": "card2",
    },
    {
        "asset_path": "assets/modify_rental.png",
        "page_link": "ui_pages/manage_rental.py",
        "key": "card3",
    },
    {
        "asset_path": "assets/complete_rental.png",
        "page_link": "ui_pages/manage_rental.py",
        "key": "card4",
    },
    {
        "asset_path": "assets/admin_options.png",
        "page_link": "ui_pages/new_reservation.py",
        "key": "card5",
    },

]

for col, info in zip(cols, card_info):
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), info["asset_path"]), "rb") as f:
        data = f.read()
        encoded = base64.b64encode(data)
    data = "data:image/png;base64," + encoded.decode("utf-8")
    with col:
        card(
            title="",
            text="",
            styles={
                "title": {
                    "font-size": "20px",
                    "fontFamily": "sans-serif",
                },
                "text": {
                    "font-size": "20px",
                },
                "card": {
                    "width": "100%",
                    "height": "50px",
                    "margin": "5px 5px 5px 5px",
                },
                "filter": {
                    "background-color": "rgba(0, 0, 0, 0)",
                },
            },
            image=data,
            key=info["key"],
            on_click=partial(st.switch_page, page=info["page_link"]),
        )

reservations_tab, rentals_tab = st.tabs(["Reservations", "Rentals"])

with reservations_tab:
    reservations = data_service.get_reservations_on_date(CNEDates.get_default_date())
    if reservations.empty:
        st.warning(
            f"**No Reservations Today**: There are no reservations for "
            f"{CNEDates.get_default_date().strftime('%b %d, %Y')}."
        )
    else:
        scooter_reservations, wheelchair_reservations = (
            reservations[reservations["device_type"] == DeviceType.SCOOTER],
            reservations[reservations["device_type"] == DeviceType.WHEELCHAIR],
        )
        st.subheader(f"Today's {DeviceType.SCOOTER} Reservations")
        display_reservations(scooter_reservations, device_type=DeviceType.SCOOTER)
        st.subheader(f"Today's {DeviceType.WHEELCHAIR} Reservations")
        display_reservations(wheelchair_reservations, device_type=DeviceType.WHEELCHAIR)

with rentals_tab:
    rentals = data_service.get_rentals_on_date(CNEDates.get_default_date())
    if rentals.empty:
        st.warning(
            f"**No Rentals Today**: There are no rentals for "
            f"{CNEDates.get_default_date().strftime('%b %d, %Y')}."
        )
    else:
        scooter_rentals, wheelchair_rentals = (
            rentals[rentals["device_type"] == DeviceType.SCOOTER],
            rentals[rentals["device_type"] == DeviceType.WHEELCHAIR],
        )
        st.subheader(f"Today's {DeviceType.SCOOTER} Rentals")
        display_rentals(scooter_rentals, device_type=DeviceType.SCOOTER)
        st.subheader(f"Today's {DeviceType.WHEELCHAIR} Rentals")
        display_rentals(wheelchair_rentals, device_type=DeviceType.WHEELCHAIR)
