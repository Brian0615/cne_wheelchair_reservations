import itertools

import pandas as pd
import streamlit as st

from common.constants import DeviceType, Location
from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates
from ui.src.data_service import DataService
from ui.src.reservation_utils import create_reservation_availability_chart

initialize_page(page_header="Reservation Availability")
data_service = DataService()
reservation_counts = data_service.get_reservation_count()
default_table = pd.DataFrame(
    list(itertools.product(CNEDates.get_cne_date_list(), [x.value for x in DeviceType], [x.value for x in Location])),
    columns=["date", "device_type", "location"],
)
default_table["date"] = pd.to_datetime(default_table["date"])
reservation_counts = default_table.merge(reservation_counts, on=["date", "device_type", "location"], how="left")
reservation_counts = reservation_counts.fillna(0).sort_values(by=["date", "device_type", "location"])

cols = st.columns(len(DeviceType), gap="large")
for col, device_type in zip(cols, DeviceType):
    with col:
        st.subheader(device_type.title() + " Availability")
        setting_key = f"{device_type.lower()}_reservation_limit"
        limit = int(data_service.get_setting(setting_id=setting_key))
        st.info(f"**Reservation Limit**: Maximum of **{limit}** reservations allowed for {device_type}s")

        if "cne-admin" in st.session_state["auth_groups"]:
            with st.expander("Set Reservation Limit for " + device_type.title() + "s", expanded=False):
                new_limit = st.number_input(
                    f"Set {device_type.title()} Reservation Limit",
                    min_value=0,
                    step=1,
                    value=int(limit) if limit is not None else 0,
                )
                if st.button(f"Update {device_type.title()} Reservation Limit"):
                    data_service.update_settings({setting_key: new_limit})
                    st.toast(f"**Success!** {device_type.title()} reservation limit updated to {new_limit}.")
                    st.rerun()

        create_reservation_availability_chart(
            reservation_counts=reservation_counts,
            device_type=device_type,
            limit=limit,
        )
