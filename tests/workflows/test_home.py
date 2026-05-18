import requests
from typing import Literal

from streamlit.testing.v1 import AppTest

from common.constants import DeviceType, Location
from tests.shared_mock_data import (
    MOCK_SCOOTER_RENTALS,
    MOCK_SCOOTER_RENTALS_PG,
    MOCK_SCOOTER_RESERVATIONS,
    MOCK_WHEELCHAIR_RENTALS,
    MOCK_WHEELCHAIR_RENTALS_PG,
    MOCK_WHEELCHAIR_RESERVATIONS,
)
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses


class _ConnectionErrorResponses:
    """Mock that simulates all API calls failing with ConnectionError."""

    def get(self, url, *args, **kwargs):
        raise requests.ConnectionError("API unreachable")

    def post(self, url, *args, **kwargs):
        raise requests.ConnectionError("API unreachable")

    def put(self, url, *args, **kwargs):
        raise requests.ConnectionError("API unreachable")


class HomeWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Home page."""

    page_path = "ui/ui_pages/home.py"

    _ALL_RESERVATIONS = MOCK_SCOOTER_RESERVATIONS + MOCK_WHEELCHAIR_RESERVATIONS
    _ALL_RENTALS = MOCK_SCOOTER_RENTALS + MOCK_WHEELCHAIR_RENTALS + MOCK_SCOOTER_RENTALS_PG + MOCK_WHEELCHAIR_RENTALS_PG

    def _assert_no_data_warning_and_no_dataframe(self, at: AppTest):
        """Assert that no data warnings are shown and no dataframes are displayed."""
        self.assertGreater(len(at.warning), 0, "Expected warning messages when there is no data")
        self.assertEqual(0, len(at.dataframe), "No dataframes should be shown when there is no data")

    def _assert_data_present_without_no_data_warning(self, at: AppTest, data_type: Literal["Rentals", "Reservations"]):
        """Assert that data is present and no 'No X Today' warning is shown."""
        self.assertFalse(
            any(f"No {data_type} Today" in w.value for w in at.warning),
            f"Should not show 'No {data_type} Today' when {data_type.lower()} exist",
        )
        self.assertGreater(len(at.dataframe), 0, f"{data_type} table should be displayed")

    def _assert_single_device_type_warnings(
            self,
            at: AppTest,
            data_type: Literal["Rentals", "Reservations"],
            device_type: str,
            other_device_type: str,
    ):
        """Assert that only one device type shows data and a warning is shown for the missing type."""
        self.assertFalse(
            any(f"No {device_type} {data_type}" in w.value for w in at.warning),
            f"Should not warn about missing {device_type} {data_type.lower()} when they exist",
        )
        self.assertTrue(
            any(f"No {other_device_type} {data_type}" in w.value for w in at.warning),
            f"Should warn about missing {other_device_type} {data_type.lower()}",
        )
        self.assertEqual(1, len(at.dataframe), f"Exactly one {data_type.lower()} table should be shown")

    def _assert_indicator_chart_shown_for_location(
            self,
            at: AppTest,
            caption_keyword: str,
            warning_prefix: str,
            location: Location,
            other_location: Location,
    ):
        """Assert that an indicator chart caption exists for the given location and a warning for the other."""
        captions = [c for c in at.caption if caption_keyword in c.value]
        self.assertEqual(1, len(captions), f"Expected one indicator chart for {location}")
        self.assertTrue(
            any(f"{warning_prefix} {other_location}" in w.value for w in at.warning),
            f"Expected indicator warning for {other_location}",
        )

    def test_no_data_shows_warnings(self):
        """When there are no rentals or reservations today, warning messages are displayed."""
        at = self._run(MockAPIResponses())
        self._assert_no_data_warning_and_no_dataframe(at)

    def test_with_reservations_today(self):
        """When reservations exist today, tables are displayed without 'no data' warnings."""
        responses = MockAPIResponses(reservations=MOCK_SCOOTER_RESERVATIONS)
        at = self._run(responses)
        self._assert_data_present_without_no_data_warning(at, "Reservations")

    def test_with_rentals_today(self):
        """When rentals exist today, rental tables are displayed without 'no data' warnings."""
        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS)
        at = self._run(responses)
        self._assert_data_present_without_no_data_warning(at, "Rentals")

    def test_single_device_type_reservations_shows_warning_for_other(self):
        """When only one device type has reservations, a warning is shown for the other type."""
        for device_reservations, device_name, other_device_name in [
            (MOCK_SCOOTER_RESERVATIONS, "Scooter", "Wheelchair"),
            (MOCK_WHEELCHAIR_RESERVATIONS, "Wheelchair", "Scooter"),
        ]:
            with self.subTest(device=device_name):
                responses = MockAPIResponses(reservations=device_reservations)
                at = self._run(responses)
                self._assert_single_device_type_warnings(at, "Reservations", device_name, other_device_name)

    def test_single_device_type_rentals_shows_warning_for_other(self):
        """When only one device type has rentals, a warning is shown for the other type."""
        for device_rentals, device_name, other_device_name in [
            (MOCK_SCOOTER_RENTALS, "Scooter", "Wheelchair"),
            (MOCK_WHEELCHAIR_RENTALS, "Wheelchair", "Scooter"),
        ]:
            with self.subTest(device=device_name):
                responses = MockAPIResponses(rentals=device_rentals)
                at = self._run(responses)
                self._assert_single_device_type_warnings(at, "Rentals", device_name, other_device_name)

    def test_no_data_shows_no_indicator_charts(self):
        """When there are no rentals or reservations, no indicator chart captions are displayed."""
        at = self._run(MockAPIResponses())
        indicator_captions = [c for c in at.caption if "Picked Up" in c.value or "Completed" in c.value]
        self.assertEqual(0, len(indicator_captions), "No indicator chart captions should appear when there is no data")

    def test_reservation_indicator_chart_shown_for_each_device_type_and_location(self):
        """For every (device_type, location) pair, the reservation indicator chart is shown for that location
        and a warning is shown for the other location."""
        for device_type in DeviceType:
            for location in Location:
                with self.subTest(device_type=device_type, location=location):
                    other_location = next(loc for loc in Location if loc != location)
                    filtered = [
                        r for r in self._ALL_RESERVATIONS
                        if r["device_type"] == device_type.value and r["location"] == location.value
                    ]
                    at = self._run(MockAPIResponses(reservations=filtered))
                    self._assert_indicator_chart_shown_for_location(at, "Picked Up", "No reservations at", location,
                                                                    other_location)

    def test_rental_indicator_chart_shown_for_each_device_type_and_location(self):
        """For every (device_type, location) pair, the rental indicator chart is shown for that location
        and a warning is shown for the other location."""
        for device_type in DeviceType:
            for location in Location:
                with self.subTest(device_type=device_type, location=location):
                    other_location = next(loc for loc in Location if loc != location)
                    filtered = [
                        r for r in self._ALL_RENTALS
                        if r["device_type"] == device_type.value and r["pickup_location"] == location.value
                    ]
                    at = self._run(MockAPIResponses(rentals=filtered))
                    self._assert_indicator_chart_shown_for_location(at, "Completed", "No rentals at", location,
                                                                    other_location)

    def test_api_unavailable_shows_error(self):
        """When the API is unreachable, an error message is displayed and the page does not crash."""
        at = self._run(_ConnectionErrorResponses(), allow_errors=True)
        self.assertGreater(len(at.error), 0, "An error message should be shown when the API is unreachable")
