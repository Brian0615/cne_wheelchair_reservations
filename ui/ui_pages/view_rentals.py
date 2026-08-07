import streamlit as st

from ui.src.auth_utils import initialize_page
from ui.src.constants import Page
from ui.src.data_service import DataService
from ui.src.display_utils import display_rentals_or_reservations_on_date
from ui.src.rental_utils import export_late_returns_to_pdf
from ui.src.utils import get_date_input

initialize_page(page_header="Rentals")

col1, _, col2 = st.columns([1, 2, 1], vertical_alignment="bottom")
view_date = get_date_input(label="View Rentals for:", key_prefix="view_rentals", col=col1)
rentals = DataService().get_rentals_on_date(rental_date=view_date)

# Add late returns export button in col2 - only enabled if there are unreturned rentals
with col2:
    if not rentals.empty and rentals["return_time"].isna().any():
        pdf_data = export_late_returns_to_pdf(rentals.copy(), view_date)
        formatted_date = view_date.strftime("%Y-%m-%d")
        st.download_button(
            label=":material/download: Download Late Returns",
            data=pdf_data,
            file_name=f"late_returns_{formatted_date}.pdf",
            mime="application/pdf",
            width="stretch"
        )

# Display rentals table
display_rentals_or_reservations_on_date(
    view_date=view_date,
    rentals_or_reservations=rentals,
    page=Page.VIEW_RENTALS,
)
