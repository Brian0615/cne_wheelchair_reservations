import streamlit as st

from common.constants import DeviceType
from src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.utils import display_reservations

st.set_page_config(layout="wide")
data_service = DataService()

today_date = CNEDates.get_default_date()
today_reservations = data_service.get_reservations_on_date(today_date)
st.subheader(f"Today's {DeviceType.SCOOTER} Reservations")
display_reservations(today_reservations, device_type=DeviceType.SCOOTER)
st.subheader(f"Today's {DeviceType.WHEELCHAIR} Reservations")
display_reservations(today_reservations, device_type=DeviceType.WHEELCHAIR)
