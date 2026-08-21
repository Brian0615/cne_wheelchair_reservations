from tests.unit.base_tests import BaseTestCases
from tests.unit.mock_requests import MockRequests


class TestHome(BaseTestCases.BaseUIPageTest):
    """Class for testing the Home page"""

    def setUp(self):
        self.page_path = "ui/ui_pages/home.py"

    def test_gauge_titles_keep_the_default_font_size(self):
        """The Home page's gauge titles should keep the original default font size, unaffected by
        the Inventory Dashboard's larger override (see the paired assertion in
        TestInventoryDashboard)."""
        gauge_figs = self._get_mock_reservations_gauge_figs()
        self.assertGreater(len(gauge_figs), 0, "At least one gauge chart should have rendered")
        for fig in gauge_figs:
            for trace in fig.data:
                self.assertEqual(14, trace.title.font.size)

    def test_gauge_chart_height_keeps_the_default(self):
        """The Home page's gauge charts should keep the original default height, unaffected by the
        Inventory Dashboard's taller override (see the paired assertion in
        TestInventoryDashboard)."""
        gauge_figs = self._get_mock_reservations_gauge_figs()
        self.assertGreater(len(gauge_figs), 0, "At least one gauge chart should have rendered")
        for fig in gauge_figs:
            self.assertEqual(75, fig.layout.height)

    def test_gauge_captions_keep_the_default_style(self):
        """The Home page's reservation/rental captions should render via plain st.caption (not the
        larger custom markdown span), unaffected by the Inventory Dashboard's larger override (see
        the paired assertion in TestInventoryDashboard)."""
        at = self._run_with_mock_reservations()

        self.assertTrue(
            any("Picked Up / Total Reservations" == caption.value for caption in at.caption),
            "The reservation caption should render via plain st.caption",
        )
        self.assertFalse(
            any("Picked Up / Total Reservations" in markdown.value for markdown in at.markdown),
            "The reservation caption should not render as a custom-font markdown span",
        )

    def test_no_show_reservations_excluded_from_gauge_total(self):
        """A No Show reservation should not count toward the gauge's total (or picked-up value),
        matching Cancelled/Waitlisted's treatment. The BLC scooter fixture has 4 non-cancelled
        reservations (Reserved, Confirmed, Completed, No Show), of which only the Completed one
        should count toward the numerator, and the No Show one should not count toward the total."""
        gauge_figs = self._get_mock_reservations_gauge_figs()
        blc_scooter_trace = gauge_figs[0].data[0]
        self.assertEqual(1, blc_scooter_trace.value, "Only the Completed reservation should count as picked up")
        self.assertEqual(" / 3", blc_scooter_trace.number.suffix, "The No Show reservation should not count toward the total")

    def test_gauge_badge_tags_keep_the_default_font_size(self):
        """The Home page's 'BLC/PG Reservations/Rentals' badge tags should keep st.badge's default
        styling, unaffected by the Inventory Dashboard's font-size override (see the paired
        assertion in TestInventoryDashboard)."""
        at = self._run_app_test_with_mock_requests(mock_requests=MockRequests())

        self.assertFalse(
            any("stMarkdownBadge" in markdown.value for markdown in at.markdown),
            "No badge font-size override should be injected on the Home page",
        )
