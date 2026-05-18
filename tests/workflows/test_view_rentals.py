from tests.shared_mock_data import MOCK_SCOOTER_RENTALS, MOCK_WHEELCHAIR_RENTALS
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses
from ui.src.constants import CNEDates


class ViewRentalsWorkflowTests(WorkflowTestCase):
    """Workflow tests for the View Rentals page."""

    page_path = "ui/ui_pages/view_rentals.py"

    def test_date_input_defaults_to_today(self):
        """Date picker defaults to today (bounded by CNE dates)."""
        at = self._run(MockAPIResponses())
        date_input = at.date_input(key="view_rentals_date")
        self.assertEqual(CNEDates.get_default_date(), date_input.value)
        cne_start, cne_end = CNEDates.get_cne_start_end_dates()
        self.assertEqual(cne_start.date(), date_input.min)
        self.assertEqual(cne_end.date(), date_input.max)

    def test_no_rentals_shows_warning(self):
        """When there are no rentals on the selected date, a warning is displayed."""
        at = self._run(MockAPIResponses())
        self.assertTrue(
            any("No Rentals" in w.value for w in at.warning),
            "Expected a 'No Rentals' warning when no rentals exist",
        )
        self.assertEqual(0, len(at.dataframe), "No dataframes should be shown when there are no rentals")

    def test_rentals_displayed(self):
        """When rentals exist for the selected date, rental tables are displayed."""
        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS)
        at = self._run(responses)
        self.assertFalse(
            any("No Rentals" in w.value for w in at.warning),
            "Should not show 'No Rentals' warning when rentals exist",
        )
        self.assertGreater(len(at.dataframe), 0, "Rental dataframe should be displayed")

    def test_single_device_type_rentals_shows_warning_for_other(self):
        """When only one device type has rentals, a warning is shown for the other device type."""
        for rentals, device_name, other_name in [
            (MOCK_SCOOTER_RENTALS, "Scooter", "Wheelchair"),
            (MOCK_WHEELCHAIR_RENTALS, "Wheelchair", "Scooter"),
        ]:
            with self.subTest(device=device_name):
                at = self._run(MockAPIResponses(rentals=rentals))
                self.assertFalse(
                    any(f"No {device_name} Rentals" in w.value for w in at.warning),
                    f"Should not warn about {device_name} rentals when they exist",
                )
                self.assertTrue(
                    any(f"No {other_name} Rentals" in w.value for w in at.warning),
                    f"Should warn that there are no {other_name} rentals",
                )
                self.assertEqual(1, len(at.dataframe), "Exactly one device type table should be shown")
