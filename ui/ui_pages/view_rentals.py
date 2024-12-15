from ui.src.auth_utils import initialize_page
from ui.src.constants import Page
from ui.src.data_service import DataService
from ui.src.utils import display_rentals_or_reservations_on_date, get_date_input


initialize_page(page_header="Rentals")

view_date = get_date_input(label="View Rentals for:")
rentals = DataService().get_rentals_on_date(date=view_date)

display_rentals_or_reservations_on_date(
    view_date=view_date,
    rentals_or_reservations=rentals,
    page=Page.VIEW_RENTALS,
)
