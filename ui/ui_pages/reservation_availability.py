import streamlit as st

from common.constants import DeviceType
from ui.src.auth_utils import initialize_page
from ui.src.constants import DEFAULT_RESERVATION_LIMIT
from ui.src.data_service import DataService
from ui.src.reservation_utils import create_reservation_availability_chart, get_reservation_counts

initialize_page(page_header="Reservation Availability")
data_service = DataService()
reservation_counts = get_reservation_counts()

cols = st.columns(len(DeviceType), gap="large")
for col, device_type in zip(cols, DeviceType):
    with col:
        st.subheader(device_type.title() + " Availability")
        setting_key = f"{device_type.lower()}_reservation_limit"
        limit = data_service.get_setting(setting_id=setting_key)
        limit = int(limit) if limit is not None else DEFAULT_RESERVATION_LIMIT
        st.info(f"**Reservation Limit**: Maximum of **{limit}** reservations allowed for {device_type}s")

        if "cne-admin" in st.session_state["auth_groups"]:
            with st.expander("Modify Reservation Limit for " + device_type.title() + "s", expanded=False):
                new_limit = st.number_input(
                    f"New {device_type.title()} Reservation Limit",
                    min_value=1,
                    step=1,
                    value=limit,
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
