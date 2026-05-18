from datetime import time

from tests.workflows.base import WorkflowTestCase
from tests.workflows.mock_responses import (
    MockAPIResponses,
    MOCK_SCOOTER_RENTALS,
    MOCK_IN_PROGRESS_RENTAL_WITH_ITEMS,
)
from common.constants import Location

# Only the in-progress rental (no items left behind)
_IN_PROGRESS_RENTALS = [r for r in MOCK_SCOOTER_RENTALS if r["status"] == "In Progress"]
# Both in-progress rentals: one without items, one with items
_IN_PROGRESS_MIXED = _IN_PROGRESS_RENTALS + [MOCK_IN_PROGRESS_RENTAL_WITH_ITEMS]


class CompleteRentalWorkflowTests(WorkflowTestCase):
    """Workflow tests for the Complete Rental page."""

    page_path = "ui/ui_pages/complete_rental.py"

    def _run_as_editor(self, responses, at=None, allow_errors=False):
        return self._run(responses, at=at, allow_errors=allow_errors, roles=["editor"])

    def _select_rental(self, responses, index=0):
        """Helper: run page and select a rental by index."""
        at = self._run_as_editor(responses)
        at.selectbox(key="complete_rental_rental_selection").select_index(index)
        at = self._run_as_editor(responses, at=at)
        return at

    # ── Happy path: no items left behind ────────────────────────────────────

    def test_no_in_progress_rentals_shows_warning(self):
        """When no in-progress rentals exist, a warning is shown and the form does not render."""
        at = self._run_as_editor(MockAPIResponses())
        self.assertTrue(
            any("No Rentals" in w.value for w in at.warning),
            "Expected a 'No Rentals' warning when no in-progress rentals exist",
        )

    def test_rental_selection_appears_when_rentals_exist(self):
        """When in-progress rentals exist, a rental selection dropdown is rendered."""
        responses = MockAPIResponses(rentals=_IN_PROGRESS_RENTALS)
        at = self._run_as_editor(responses)
        self.assertFalse(
            any("No Rentals" in w.value for w in at.warning),
            "Should not show 'No Rentals' warning when in-progress rentals exist",
        )
        selection_boxes = [s for s in at.selectbox if "complete_rental_rental_selection" in s.key]
        self.assertGreater(len(selection_boxes), 0, "Rental selection dropdown should be present")

    def test_rental_selection_count_matches_in_progress_only(self):
        """The dropdown shows exactly the number of in-progress rentals."""
        responses = MockAPIResponses(rentals=_IN_PROGRESS_MIXED)
        at = self._run_as_editor(responses)
        options = at.selectbox(key="complete_rental_rental_selection").options
        self.assertEqual(
            len(_IN_PROGRESS_MIXED),
            len(options),
            "Dropdown should show exactly the in-progress rentals",
        )

    def test_form_renders_after_rental_selected(self):
        """After selecting an in-progress rental, the complete rental form is shown."""
        responses = MockAPIResponses(rentals=_IN_PROGRESS_RENTALS)
        at = self._select_rental(responses)
        self.assertGreater(len(at.date_input), 0, "Return date input should be visible after rental selected")
        self.assertGreater(len(at.time_input), 0, "Return time input should be visible after rental selected")

    def test_no_items_left_behind_shows_one_checkbox(self):
        """A rental without items left behind shows only the deposit checkbox."""
        responses = MockAPIResponses(rentals=_IN_PROGRESS_RENTALS)
        at = self._select_rental(responses, index=0)
        self.assertEqual(1, len(at.checkbox), "Only the deposit checkbox should appear when no items left behind")
        self.assertIn("Deposit", at.checkbox[0].label, "Single checkbox should be the deposit confirmation")

    # ── Happy path: with items left behind ──────────────────────────────────

    def test_rental_with_items_left_behind_shows_two_checkboxes(self):
        """A rental with items left behind shows an items checkbox and a deposit checkbox."""
        responses = MockAPIResponses(rentals=_IN_PROGRESS_MIXED)
        # Index 1 has items left behind (MOCK_IN_PROGRESS_RENTAL_WITH_ITEMS)
        at = self._select_rental(responses, index=1)
        self.assertEqual(2, len(at.checkbox), "Two checkboxes should appear when items left behind")
        labels = [cb.label for cb in at.checkbox]
        self.assertTrue(
            any("Items Left Behind" in lbl or "Walker" in lbl for lbl in labels),
            "One checkbox should reference the items left behind",
        )
        self.assertTrue(
            any("Deposit" in lbl for lbl in labels),
            "One checkbox should be the deposit confirmation",
        )

    def test_items_left_behind_checkbox_blocks_submit_when_unchecked(self):
        """The submit button stays disabled until both the items and deposit checkboxes are checked."""
        responses = MockAPIResponses(rentals=_IN_PROGRESS_MIXED)
        at = self._select_rental(responses, index=1)

        at.time_input(key="complete_rental_return_time").set_value(time(14, 30))
        at.selectbox(key="complete_rental_return_location").set_value(Location.PG)
        at.text_input(key="complete_rental_staff_name").set_value("Test Staff")
        at = self._run_as_editor(responses, at=at)

        # Check deposit only — items still unchecked
        deposit_cb = [cb for cb in at.checkbox if "Deposit" in cb.label][0]
        deposit_cb.set_value(True)
        at = self._run_as_editor(responses, at=at)
        self.assertTrue(
            at.button(key="complete_rental_submit").disabled,
            "Submit should remain disabled until items left behind are also confirmed",
        )

    # ── Edge case: submit button gating ─────────────────────────────────────

    def test_deposit_not_confirmed_blocks_submit(self):
        """The submit button is disabled when the deposit received checkbox is not checked."""
        responses = MockAPIResponses(rentals=_IN_PROGRESS_RENTALS)
        at = self._select_rental(responses)
        submit_buttons = [b for b in at.button if "complete_rental_submit" in b.key]
        if submit_buttons:
            self.assertTrue(
                all(b.disabled for b in submit_buttons),
                "Submit button should be disabled when deposit is not confirmed",
            )

    def test_submit_enabled_only_when_all_fields_filled(self):
        """Submit button becomes enabled only after return time, location, staff name, and deposit are all set."""
        responses = MockAPIResponses(rentals=_IN_PROGRESS_RENTALS)
        at = self._select_rental(responses)
        self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit should start disabled")

        at.time_input(key="complete_rental_return_time").set_value(time(14, 30))
        at = self._run_as_editor(responses, at=at)
        self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit still disabled without location")

        at.selectbox(key="complete_rental_return_location").set_value(Location.PG)
        at = self._run_as_editor(responses, at=at)
        self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit still disabled without staff name")

        at.text_input(key="complete_rental_staff_name").set_value("Test Staff")
        at = self._run_as_editor(responses, at=at)
        self.assertTrue(at.button(key="complete_rental_submit").disabled, "Submit still disabled without deposit")

        at.checkbox[0].set_value(True)
        at = self._run_as_editor(responses, at=at)
        self.assertFalse(at.button(key="complete_rental_submit").disabled,
                         "Submit should be enabled once all fields filled")
