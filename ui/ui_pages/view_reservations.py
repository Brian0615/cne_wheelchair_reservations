import datetime

from ui.src.auth_utils import initialize_page
from ui.src.constants import CNEDates, Page
from ui.src.data_service import DataService
from ui.src.utils import display_rentals_or_reservations

initialize_page(page_header="Reservations")

# create tabs
all_dates = CNEDates.get_cne_date_list(year=datetime.datetime.today().year)
today_date = CNEDates.get_default_date()
all_dates = all_dates[all_dates.index(today_date):] + [" "] * 3 + all_dates[:all_dates.index(today_date)]

display_rentals_or_reservations(
    dates_list=all_dates,
    all_rentals_or_reservations=DataService().get_all_reservations(),
    page=Page.VIEW_RESERVATIONS
)
