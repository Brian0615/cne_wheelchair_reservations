import streamlit as st

from common.constants import DeviceType, Location
from common.cne_dates import CNEDates
from ui.src.auth_utils import initialize_page
from ui.src.data_service import DataService
from ui.src.device_utils import (
    create_dashboard_inventory_chart,
    create_dashboard_legend_chart,
    get_dashboard_chart_column_weight,
)
from ui.src.display_utils import display_dual_indicator_rental_chart, display_dual_indicator_reservation_chart

initialize_page()

# Larger than display_dual_indicator_chart's defaults (title 14, caption via st.caption, height 75)
# so this page's gauge cards match its other enlarged chart text. Scoped to this page only -- the
# Home page's gauge cards keep the smaller defaults. chart_height is bumped along with the title
# font so the larger title text has room to render without being clipped at the top of the chart.
_GAUGE_TITLE_FONT_SIZE = 20
_GAUGE_CAPTION_FONT_SIZE = 20
_GAUGE_CHART_HEIGHT = 150
# st.badge (the "BLC/PG Reservations/Rentals" tags) has no font-size parameter of its own -- it
# renders as a ":color-badge[...]" Markdown directive with its font-size set inline by Streamlit,
# so overriding it needs a CSS rule with !important. Injecting it here (rather than editing
# Streamlit's own CSS) keeps the override scoped to this page's script run -- it's not present in
# the Home page's DOM at all.
_GAUGE_BADGE_FONT_SIZE = 20


def _render_gauge_cards(reservations, rentals):
    """Render the same BLC/PG reservation and rental gauge cards shown on the Home page."""
    st.markdown(
        f"<style>.stMarkdownBadge {{ font-size: {_GAUGE_BADGE_FONT_SIZE}px !important; }}</style>",
        unsafe_allow_html=True,
    )
    reservations_col1, reservations_col2, rentals_col1, rentals_col2 = st.columns(4)
    for col, location, colour in zip([reservations_col1, reservations_col2], Location, ["orange", "violet"]):
        with col, st.container(border=True):
            st.badge(f"{location} Reservations", color=colour)
            display_dual_indicator_reservation_chart(
                reservations=reservations,
                location=location,
                title_font_size=_GAUGE_TITLE_FONT_SIZE,
                caption_font_size=_GAUGE_CAPTION_FONT_SIZE,
                chart_height=_GAUGE_CHART_HEIGHT,
            )
    for col, location, colour in zip([rentals_col1, rentals_col2], Location, ["orange", "violet"]):
        with col, st.container(border=True):
            st.badge(f"{location} Rentals", color=colour)
            display_dual_indicator_rental_chart(
                rentals=rentals,
                location=location,
                title_font_size=_GAUGE_TITLE_FONT_SIZE,
                caption_font_size=_GAUGE_CAPTION_FONT_SIZE,
                chart_height=_GAUGE_CHART_HEIGHT,
            )


def _render_inventory_charts(scooter_inventory, wheelchair_inventory):
    """Render the colour-coded status chart for each device type, one per column. Column
    widths are weighted by each chart's actual rendered width (in row-blocks of up to 10
    devices each, matching create_dashboard_inventory_chart's wraparound), not raw device
    count, so e.g. 11 devices (2 blocks) get twice the space of 9 devices (1 block).
    """
    column_weights = [
        get_dashboard_chart_column_weight(scooter_inventory),
        get_dashboard_chart_column_weight(wheelchair_inventory),
    ]
    scooter_col, wheelchair_col = st.columns(column_weights, gap="small")
    for device_type, col, inventory in zip(
            [DeviceType.SCOOTER, DeviceType.WHEELCHAIR],
            [scooter_col, wheelchair_col],
            [scooter_inventory, wheelchair_inventory],
    ):
        with col:
            with st.container(border=True):
                st.subheader(f"{device_type}s")
                if inventory.empty:
                    st.caption(f"No {device_type}s in inventory")
                    continue
                chart = create_dashboard_inventory_chart(inventory)
                st.plotly_chart(chart, config={'displayModeBar': False})


@st.fragment(run_every="30s")
def _render_dashboard():
    """Fetch the latest data and render the dashboard.

    Runs on its own timer via st.fragment(run_every=...) so only this fragment reruns
    every 30s -- the sidebar (Welcome/Logout/version, from initialize_page() above) is
    not rerun on each tick.
    """
    # get_full_inventory/get_reservations_on_date/get_rentals_on_date are cached with ttl=30s
    # for other pages. That's stacked with a 30s fragment tick here could show data up to ~60s
    # stale in the worst case -- and since st.cache_data is process-global, calling .clear() on
    # them would also evict that cache for every other concurrent session/page. The *_bypass_cache
    # variants fetch fresh data on every call without touching the shared cache at all.
    data_service = DataService()
    full_inventory = data_service.get_full_inventory_bypass_cache()
    reservations = data_service.get_reservations_on_date_bypass_cache(CNEDates.get_default_date())
    rentals = data_service.get_rentals_on_date_bypass_cache(CNEDates.get_default_date())
    if full_inventory is None:
        st.error("**Error**: Unable to load inventory. Please try again later.")
        return

    _render_gauge_cards(reservations, rentals)
    _render_inventory_charts(*full_inventory)
    with st.container(border=True):
        st.plotly_chart(create_dashboard_legend_chart(), config={'displayModeBar': False})


_render_dashboard()
