from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import (
    MockAPIResponses,
    MOCK_SCOOTER_RESERVATIONS,
    MOCK_SCOOTER_RENTALS,
    MOCK_WHEELCHAIR_RESERVATIONS,
    MOCK_WHEELCHAIR_RENTALS,
)


class HomeWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Home page."""

    page_path = "ui/ui_pages/home.py"

    def test_no_data_shows_warnings(self):
        """When there are no rentals or reservations today, warning messages are displayed."""
        at = self._run(MockAPIResponses())
        self.assertGreater(len(at.warning), 0, "Expected warning messages when there is no data")
        self.assertEqual(0, len(at.dataframe), "No dataframes should be shown when there is no data")

    def test_with_reservations_today(self):
        """When reservations exist today, tables are displayed without 'no data' warnings."""
        responses = MockAPIResponses(reservations=MOCK_SCOOTER_RESERVATIONS)
        at = self._run(responses)
        self.assertFalse(
            any("No Reservations Today" in w.value for w in at.warning),
            "Should not show 'No Reservations Today' when reservations exist",
        )
        self.assertGreater(len(at.dataframe), 0, "Reservation table should be displayed")

    def test_with_rentals_today(self):
        """When rentals exist today, rental tables are displayed without 'no data' warnings."""
        responses = MockAPIResponses(rentals=MOCK_SCOOTER_RENTALS)
        at = self._run(responses)
        self.assertFalse(
            any("No Rentals Today" in w.value for w in at.warning),
            "Should not show 'No Rentals Today' when rentals exist",
        )
        self.assertGreater(len(at.dataframe), 0, "Rental table should be displayed")

    def test_single_device_type_reservations_shows_warning_for_other(self):
        """When only one device type has reservations, a warning is shown for the other type."""
        for device_reservations, device_name, other_device_name in [
            (MOCK_SCOOTER_RESERVATIONS, "Scooter", "Wheelchair"),
            (MOCK_WHEELCHAIR_RESERVATIONS, "Wheelchair", "Scooter"),
        ]:
            with self.subTest(device=device_name):
                responses = MockAPIResponses(reservations=device_reservations)
                at = self._run(responses)
                self.assertFalse(
                    any(f"No {device_name} Reservations" in w.value for w in at.warning),
                    f"Should not warn about missing {device_name} reservations when they exist",
                )
                self.assertTrue(
                    any(f"No {other_device_name} Reservations" in w.value for w in at.warning),
                    f"Should warn about missing {other_device_name} reservations",
                )
                self.assertEqual(1, len(at.dataframe), "Exactly one reservation table should be shown")

    def test_single_device_type_rentals_shows_warning_for_other(self):
        """When only one device type has rentals, a warning is shown for the other type."""
        for device_rentals, device_name, other_device_name in [
            (MOCK_SCOOTER_RENTALS, "Scooter", "Wheelchair"),
            (MOCK_WHEELCHAIR_RENTALS, "Wheelchair", "Scooter"),
        ]:
            with self.subTest(device=device_name):
                responses = MockAPIResponses(rentals=device_rentals)
                at = self._run(responses)
                self.assertFalse(
                    any(f"No {device_name} Rentals" in w.value for w in at.warning),
                    f"Should not warn about missing {device_name} rentals when they exist",
                )
                self.assertTrue(
                    any(f"No {other_device_name} Rentals" in w.value for w in at.warning),
                    f"Should warn about missing {other_device_name} rentals",
                )
                self.assertEqual(1, len(at.dataframe), "Exactly one rental table should be shown")
