from unittest.mock import patch

from tests.shared_mock_data import MOCK_SCOOTER_RESERVATIONS, MOCK_WHEELCHAIR_RESERVATIONS
from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import MockAPIResponses
from ui.src.constants import CNEDates
from ui.src import reservation_utils


class ViewReservationsWorkflowTests(WorkflowTestCase):
    """Workflow tests for the View Reservations page."""

    page_path = "ui/ui_pages/view_reservations.py"

    def test_date_input_defaults_to_today(self):
        """Date picker defaults to today (bounded by CNE dates)."""
        at = self._run(MockAPIResponses())
        date_input = at.date_input(key="view_reservations_date")
        self.assertEqual(CNEDates.get_default_date(), date_input.value)
        cne_start, cne_end = CNEDates.get_cne_start_end_dates()
        self.assertEqual(cne_start.date(), date_input.min)
        self.assertEqual(cne_end.date(), date_input.max)

    def test_no_reservations_shows_warning(self):
        """When no reservations exist, a warning is displayed and no dataframes are shown."""
        at = self._run(MockAPIResponses())
        self.assertTrue(
            any("No Reservations" in w.value for w in at.warning),
            "Expected a 'No Reservations' warning when no reservations exist",
        )
        self.assertEqual(0, len(at.dataframe), "No dataframe should be shown when there are no reservations")

    def test_reservations_shown_when_data_exists(self):
        """When reservations exist for the selected date, tables are displayed."""
        responses = MockAPIResponses(reservations=MOCK_SCOOTER_RESERVATIONS)
        at = self._run(responses)
        self.assertFalse(
            any("No Reservations" in w.value for w in at.warning),
            "Should not show 'No Reservations' warning when reservations exist",
        )
        self.assertGreater(len(at.dataframe), 0, "Reservation dataframe should be displayed")

    def test_single_device_type_reservations_shows_warning_for_other(self):
        """When only one device type has reservations, a warning is shown for the other device type."""
        for reservations, device_name, other_name in [
            (MOCK_SCOOTER_RESERVATIONS, "Scooter", "Wheelchair"),
            (MOCK_WHEELCHAIR_RESERVATIONS, "Wheelchair", "Scooter"),
        ]:
            with self.subTest(device=device_name):
                at = self._run(MockAPIResponses(reservations=reservations))
                self.assertFalse(
                    any(f"No {device_name} Reservations" in w.value for w in at.warning),
                    f"Should not warn about {device_name} reservations when they exist",
                )
                self.assertTrue(
                    any(f"No {other_name} Reservations" in w.value for w in at.warning),
                    f"Should warn that there are no {other_name} reservations",
                )
                self.assertEqual(1, len(at.dataframe), "Exactly one device type table should be shown")

    def test_pdf_export_called_when_reservations_exist(self):
        """When reservations exist, the PDF export function can be triggered."""
        responses = MockAPIResponses(reservations=MOCK_SCOOTER_RESERVATIONS + MOCK_WHEELCHAIR_RESERVATIONS)
        with patch.object(reservation_utils, "export_reservations_to_pdf", return_value=b"mock_pdf") as mock_export:
            at = self._run(responses)
        # The page should load without errors
        self.assertEqual(0, len(at.error), "Page should load without errors when reservations exist")

    def test_no_reservations_shows_no_dataframe(self):
        """No dataframe is shown when there are no reservations, matching the empty state."""
        at = self._run(MockAPIResponses())
        self.assertEqual(0, len(at.dataframe), "No dataframe should be shown when no reservations exist")
