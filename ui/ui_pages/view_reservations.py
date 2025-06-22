import streamlit as st

from ui.src.auth_utils import initialize_page
from ui.src.constants import Page
from ui.src.data_service import DataService
from ui.src.display_utils import display_rentals_or_reservations_on_date
from ui.src.reservation_utils import export_reservations_to_pdf
from ui.src.utils import get_date_input

initialize_page(page_header="Reservations")

col1, _, col2 = st.columns([1, 2, 1], vertical_alignment="bottom")
view_date = get_date_input(label="View Reservations for:", key_prefix="view_reservations", col=col1)
reservations = DataService().get_reservations_on_date(date=view_date)

# Add export button in col2 - only enabled if there are reservations
with col2:
    if not reservations.empty:
        pdf_data = export_reservations_to_pdf(reservations_df=reservations, date=view_date)
        formatted_date = view_date.strftime("%Y-%m-%d")
        st.download_button(
            label=":material/download: Download Reservations",
            data=pdf_data,
            file_name=f"reservations_{formatted_date}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Display reservations table
display_rentals_or_reservations_on_date(
    view_date=view_date,
    rentals_or_reservations=reservations,
    page=Page.VIEW_RESERVATIONS,
)
