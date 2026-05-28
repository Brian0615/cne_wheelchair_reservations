from datetime import date
from unittest import TestCase

import pandas as pd
from streamlit.testing.v1 import AppTest

from common.utils import get_default_timezone
from ui.src.display_utils import coerce_pandas_aware_datetime, display_rentals_or_reservations_on_date

_TZ = get_default_timezone()
_DATE = date(2025, 8, 20)
_DEFAULT_DATE_STR = str(_DATE)


class TestCoercePandasAwareDatetime(TestCase):
    """Tests for coerce_pandas_aware_datetime."""

    def test_naive_string_converted_to_tz_aware(self):
        series = pd.Series(["2025-08-20T10:00:00+00:00"])
        result = coerce_pandas_aware_datetime(series)
        self.assertEqual(_TZ, result.dt.tz)

    def test_already_aware_timestamp_converted_to_local_tz(self):
        import pytz
        utc_time = pd.Series(
            [pd.Timestamp("2025-08-20 14:00:00", tz="UTC")]
        )
        result = coerce_pandas_aware_datetime(utc_time)
        self.assertEqual(_TZ, result.dt.tz)

    def test_invalid_values_coerced_to_nat(self):
        series = pd.Series(["not-a-date", None])
        result = coerce_pandas_aware_datetime(series)
        self.assertTrue(result.isna().all())


class TestDisplayRentalsOrReservationsOnDate(TestCase):
    """Tests for display_rentals_or_reservations_on_date."""

    def test_unsupported_page_raises_value_error(self):
        """Passing an unsupported page value raises ValueError."""
        df = pd.DataFrame()
        with self.assertRaises(ValueError):
            display_rentals_or_reservations_on_date(
                view_date=_DATE,
                rentals_or_reservations=df,
                page="unsupported_page",
            )

    def test_empty_dataframe_shows_warning(self):
        def run():
            import pandas as pd
            from datetime import date
            from ui.src.display_utils import display_rentals_or_reservations_on_date
            from ui.src.constants import Page
            display_rentals_or_reservations_on_date(
                view_date=date(2025, 8, 20),
                rentals_or_reservations=pd.DataFrame(),
                page=Page.VIEW_RENTALS,
            )

        at = AppTest.from_function(run).run()
        self.assertGreater(len(at.warning), 0, "Should show a warning for empty rentals")

    def test_none_dataframe_shows_warning(self):
        def run():
            from datetime import date
            from ui.src.display_utils import display_rentals_or_reservations_on_date
            from ui.src.constants import Page
            display_rentals_or_reservations_on_date(
                view_date=date(2025, 8, 20),
                rentals_or_reservations=None,
                page=Page.VIEW_RESERVATIONS,
            )

        at = AppTest.from_function(run).run()
        self.assertGreater(len(at.warning), 0, "Should show a warning for None reservations")

    def test_reservations_with_data_shows_subheaders(self):
        def run():
            import pandas as pd
            from datetime import date
            from common.constants import DeviceType, Location, ReservationStatus
            from ui.src.display_utils import display_rentals_or_reservations_on_date
            from ui.src.constants import Page
            reservations_df = pd.DataFrame([{
                "id": "S0820001",
                "device_type": DeviceType.SCOOTER,
                "name": "Alice Smith",
                "phone_number": "9052938402",
                "location": Location.BLC,
                "reservation_time": "2025-08-20T10:00:00-04:00",
                "status": ReservationStatus.RESERVED,
                "rental_id": None,
                "notes": "",
            }])
            display_rentals_or_reservations_on_date(
                view_date=date(2025, 8, 20),
                rentals_or_reservations=reservations_df,
                page=Page.VIEW_RESERVATIONS,
            )

        at = AppTest.from_function(run).run()
        self.assertGreater(len(at.subheader), 0, "Should show device-type subheaders")
